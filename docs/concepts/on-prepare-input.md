# OnPrepareInput — Initialzustand für die Dateneingabe

## Problem

`contacts/edit Mike` öffnet ein leeres Formular, obwohl die Daten zu "Mike"
bereits existieren. Der `FormRenderer` kennt den fachlichen Kontext nicht —
er soll ihn auch nicht kennen.

Die `Interactor`-Ebene (`intercept`) entscheidet *ob* ein Formular geöffnet
wird, hat aber keine Möglichkeit, Anfangswerte zu beschaffen.

## Architektur

```
Request
  │
  ▼
resolve node ─────────────────► Invocation
  │
  ▼
Interactor.intercept()
  │
  ├── CLI → pass through
  │
  └── FORM
        │
        ├── 1. OnPrepareInput (NEU)
        │       node, invocation, tokens, session
        │       → InvocationInput | None
        │
        ├── 2. FormRenderer.render(invocation, initial=...)
        │       → form mit Vorbelegung
        │
        └── 3. FormRenderer.bind(invocation)
                → BoundInvocation
```

## Neue Komponenten

### 1. Port-Protokoll `OnPrepareInput`

```python
class OnPrepareInput(Protocol):
    """Liefert initiale Werte für eine Invocation.

    Wird vor dem Form-Rendering gerufen. Gibt None zurück, wenn
    keine Vorbelegung existiert (identisch zu add).
    """
    async def __call__(
        self,
        *,
        node: Node,
        invocation: Invocation,
        tokens: list[str],
        session: Session,
    ) -> InvocationInput | None: ...
```

### 2. `Form.__init__` erhält `initial`-Parameter

```python
class Form:
    def __init__(
        self,
        fields: list[Param] | None = None,
        *,
        title: str = "",
        initial: dict[str, str] | None = None,   # NEU
    ):
        ...
        self.data: dict[str, str] = dict(initial or {})  # geändert
```

Die `ask()`-Methode überspringt bereits belegte Felder nicht automatisch —
das ist Absicht: der User sieht alle Felder und kann sie überschreiben.
Das aktive Feld ist das erste mit `None`-Wert (Client-Logik, bereits
vorhanden).

### 3. `FormRenderer.render()` nimmt `initial` entgegen

```python
class FormRenderer:
    async def render(
        self,
        invocation: Invocation,
        initial: InvocationInput | None = None,   # NEU
    ) -> ...:
        all_fields = list(invocation.args) + list(invocation.options)
        form = Form(
            fields=all_fields,
            title=invocation.action or "",
            initial=dict(initial.values) if initial else None,  # NEU
        )
        ...
```

### 4. `Interactor` bekommt `on_prepare_input`-Port

```python
class Interactor:
    def __init__(
        self,
        on_form_render: OnFormRender,
        on_form_bind: OnFormBind,
        on_prepare_input: OnPrepareInput | None = None,  # NEU
    ):
        ...
```

### 5. `Interactor._run_form()` ruft Port vor dem Rendern

```python
async def _run_form(  # NEU: async
    self,
    node: Node,
    tokens: list[str],
    session: Session,
) -> tuple[Node, list[str]]:
    inv = _matched_invocation(node)
    if inv is None:
        return node, tokens

    # ── Vorbelegung holen ─────────────────────────────────
    initial = None
    if self._on_prepare_input is not None:
        initial = await self._on_prepare_input(
            node=node,
            invocation=inv,
            tokens=tokens,
            session=session,
        )

    form_node = Node(
        key=node.key,
        run=self._make_form_handler(node, inv, initial),  # NEU: initial
        ports=node.ports,
        parent=node.parent,
    )
    return form_node, []
```

### 6. `_make_form_handler` reicht `initial` an `render` weiter

```python
def _make_form_handler(self, original_node, inv, initial=None):
    async def handler(space):
        async for outcome in self._on_form_render(inv, initial=initial):
            yield outcome
        bound = self._on_form_bind(inv)
        req = RequestBuilder().build(
            bound, command=original_node.key, lang=space.session.lang
        )
        yield Outcome(control=Continue(), next_steps=[req])
    return handler
```

### 7. Intercept muss `_run_form` awaiten

```python
async def intercept(self, node, tokens, session, context):
    ...
    return await self._run_form(node, tokens, session)
    #      ^^^^^ geändert — _run_form ist jetzt async
```

### 8. Wire — `build_machine()` verdrahtet den Port

```python
# machine.py (wire)
interactor = Interactor(
    on_form_render=form_renderer.render,
    on_form_bind=form_renderer.bound,
    on_prepare_input=...,  # None, wenn nicht gebraucht
)
```

## Beispiel: `contacts/edit` im CRM-Space

```python
# space.py
from y5n.api.ports import OnPrepareInput
from y5n.base.nodes import InvocationInput

class ContactSpace:
    async def on_prepare_edit(self, *, node, invocation, tokens, session):
        name = tokens[0] if tokens else None
        if name is None:
            return None
        contact = await self.store.find(name)
        if contact is None:
            return None
        return InvocationInput(values={
            "name": contact.name,
            "company": contact.company,
            "phone": contact.phone,
        })

    def setup(self, platform):
        edit = platform.resolve("contacts/edit")
        edit.ports.provide(OnPrepareInput, self.on_prepare_edit)
```

## Was ist mit `contacts/duplicate`?

Der gleiche Mechanismus:

```python
class ContactSpace:
    async def on_prepare_duplicate(self, *, node, invocation, tokens, session):
        name = tokens[0] if tokens else None
        if name is None:
            return None
        contact = await self.store.find(name)
        if contact is None:
            return None
        # gleiche Werte, aber ohne ID
        return InvocationInput(values={
            "name": contact.name,
            "company": contact.company,
            "phone": contact.phone,
        })
```

Das Formular ist identisch zu `add` — nur die Vorbelegung unterscheidet sich.

## Was ist mit `contacts/import`?

```python
async def on_prepare_import(self, *, node, invocation, tokens, session):
    template = await self.store.get_template()
    return InvocationInput(values={
        "name": template.default_name,
        "company": template.default_company,
    })
```

## Vorteile

1. **Kein neuer Node-Hook** (`pre_load`), sondern ein Port — euer Pattern.
2. **FormRenderer bleibt dumm** — er bekommt nur Werte.
3. **Interactor bleibt kontextfrei** — er ruft nur einen Port.
4. **CLI und FORM teilen sich den Initialisierungsschritt** — derselbe
   `OnPrepareInput` kann auch CLI-Defaults liefern.
5. **`add`, `edit`, `duplicate`, `import`, `wizard`** — alles derselbe
   Mechanismus, kein Special-Casing.
6. **Initiale Werte sind optional** — `None` = leeres Formular.

## Änderungsübersicht

| Datei | Änderung |
|---|---|
| `base/flow/patterns/public/form.py` | `__init__` nimmt `initial: dict[str,str] \| None` |
| `runtime/interaction/form_renderer.py` | `render()` nimmt `initial: InvocationInput \| None` |
| `runtime/interaction/interactor.py` | Neuer Port `OnPrepareInput`, `_run_form` wird async, ruft Port |
| `runtime/wire/machine.py` | Optionaler Parameter in `Interactor(...)` |
| `spaces/*/space.py` | `ports.provide(OnPrepareInput, handler)` |
