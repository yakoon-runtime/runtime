# Projection Modes

## Problem

`yield out(projection)` durchläuft immer den gesamten Lebenszyklus:

```
begin_projection (PatchReset → Client löscht View)
→ emit_projection  (PatchAppendStructure)
→ finish_projection (final=True)
```

Das passt für **replace** (Formular wird in-place aktualisiert),
aber nicht für **append** (Job-Liste wächst Stück für Stück).

Gleichzeitig teilen sich alle `out()`-Aufrufe eines Flows dieselbe
`job_id = flow.id`. Es gibt keine Möglichkeit, innerhalb eines Flows
mehrere unabhängige Projektionsräume zu adressieren (z.B. Status +
Log nebeneinander).

## Analyse

Der Transport kann bereits unterscheiden:

| PatchOp | Bedeutung |
|---------|-----------|
| `PatchReset()` | Client löscht gesamten Baum für diese `job_id` |
| `PatchAppendStructure(nodes)` | Fügt neue Nodes hinzu |
| *(empty, final=True)* | Stream ist vollständig |

Es gibt **keine** `StreamProjection` oder `SnapshotProjection` als
Typ — es gibt nur eine Patch-Strategie:

> **Replace** → `begin()` mit `PatchReset` + `emit()` + `finish()`
> **Append** → `begin()` *ohne* `PatchReset` + `emit()` + `finish()`

Und es gibt keine "eine Projektion pro Flow" — es gibt nur den
`job_id`-Schlüssel, der beliebig qualifiziert werden kann.

## Lösung: `out()` mit `mode` und `space`

### Stufe 1 — Patch-Strategie

```python
yield out(projection, mode="replace")   # PatchReset + AppendStructure
yield out(projection, mode="append")    # nur AppendStructure
```

### Stufe 2 — Mehrere Räume

```python
yield out(status_projection, id="status")
yield out(log_projection, id="log")
```

→ `job_id = f"{flow.id}:status"` bzw. `f"{flow.id}:log"`

Client-seitig sind das unabhängige Projektionsbäume.

### Stufe 3 — Kombination

```python
yield out(status, id="status", mode="replace")
yield out(log_line,  id="log",    mode="append")
yield out(log_line,  id="log",    mode="append")
yield out(status, id="status", mode="replace")
```

## Änderungen

### `dsl.py`

```python
def out(
    projection: Projection,
    *,
    mode: Literal["replace", "append"] = "replace",
    space: str | None = None,
) -> Outcome:
    return Outcome(
        effects=[EmitView(projection, mode=mode, space=space)]
    )
```

Kein Auto-Wrap mehr nötig — `Outcome` hat bereits `effects`.
`out_text()` delegiert an `out()` und erbt die Parameter.

Hinweis: `mode="replace"` ist Standard, damit `yield out(text)`
weiterhin funktioniert.

### `effect.py`

```python
class EmitView(Effect):
    def __init__(self, view, persist=False, mode="replace", space=None):
        self.view = view
        self.persist = persist
        self.mode = mode
        self.space = space
```

### `engine.py: _apply_effects()`

```python
if isinstance(effect, EmitView):
    if effect.persist:
        flow.view = effect.view

    job_id = f"{flow.id}:{effect.space}" if effect.space else flow.id

    await self.on_projection(
        session=session,
        projection=effect.view,
        ctx=flow.event.context,
        job_id=job_id,
        mode=effect.mode,       # NEU
    )
```

### `stream.py: EventStreamOutput`

```python
async def send_projection(
    self, session, projection, *, ctx, job_id, mode="replace"
):
    await self.on_begin(
        session=session, projection=projection, ctx=ctx,
        job_id=job_id, reset=(mode == "replace"),
    )
    try:
        await self.on_emit(session=session, projection=projection)
    except Exception:
        await self.on_abort(...)
        raise
    else:
        await self.on_finish(session=session, projection=projection)
```

### `dispatcher.py: begin_projection()`

```python
async def begin_projection(
    self, session, projection, *, ctx, job_id, reset=True
):
    stream = _ViewStream(...)  # immer anlegen
    if reset:
        await session.emit(begin_event(...))  # mit PatchReset
```

## Nicht-Änderungen

- Keine neuen Projection-Typen
- Keine neuen Patch-Operationen
- Keine neuen Effect-Klassen
- Transport, Serialisierung, Client — unverändert
- `prompt()` weiterhin mit `persist=True` (unabhängig von mode)

## Ausblick

Sobald `mode` und `space` etabliert sind, lassen sich weitere
Patch-Strategien ergänzen:

| Mode | Verhalten |
|------|-----------|
| `replace` | Reset + AppendStructure (heute) |
| `append` | Nur AppendStructure (kein Reset) |
| `update` (Zukunft) | PatchUpdate statt Reset+Neuaufbau |
