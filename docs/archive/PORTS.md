# Ports-Mechanismus in Yakoon

## Überblick

Das Ports-System ist ein **reines Dependency-Injection-Framework** auf Basis hierarchischer Container – ohne Framework, ohne Dekorateure, ohne Magie. Es erlaubt, Capabilities (Funktionen, Dienste, Services) durch den Node-Baum zu reichen, sodass jeder Node genau das bekommt, was er braucht.

---

## Grundbaustein: `Container`

**Datei:** `runtime/y5ncore-base/src/y5n/base/runtime/container.py`

Jeder `Container` ist ein einfaches Key-Value-Store mit zwei Besonderheiten:

1. **Elternkette**: Ein Container hat einen `parent`. Wird ein Port nicht gefunden, wird beim Eltern-Container nachgesehen → **hierarchisches Lookup**.
2. **Statisch oder lazy**: Man kann fertige Instanzen binden (`bind()`) oder Fabriken (`bind_lazy()`) – lazy wird beim ersten Zugriff ausgeführt und gecached.

```python
container = Container(allow_override=True)
container.bind(MyPort, my_instance)        # statisch
container.bind_lazy(MyPort, factory_fn)    # lazy
container.get(MyPort)                      # → my_instance
```

**Methoden:**

| Methode | Beschreibung |
|---------|-------------|
| `bind(port, capability)` | Registriert eine fertige Capability-Instanz |
| `bind_lazy(port, factory)` | Registriert eine async-Fabrik (wird beim ersten `get()` ausgeführt) |
| `get(port)` | Holt Capability aus eigenem Container → Eltern → ... → Root |
| `contains(port)` | Prüft, ob Port irgendwo in der Kette existiert |
| `fork()` | Erzeugt Kind-Container mit sich selbst als Parent |
| `mount(root)` | Hängt Container-Kette an neuen Root (erweitert Lookup) |

---

## `NodePorts` – Die zwei Richtungen

**Datei:** `runtime/y5ncore-base/src/y5n/base/nodes/ports.py`

`NodePorts` kapselt **zwei** Container:

```python
class NodePorts:
    _publish_to: Container  # nach oben (für Eltern sichtbar)
    _local: Container       # lokal + nach unten (Kinder erben)
```

**API:**

| Methode | Wirkung |
|---------|---------|
| `provide(port, capability)` | Registriert im `_local` → sichtbar für diesen Node **und alle Kind-Nodes** |
| `publish(port, capability)` | Registriert im `_publish_to` → sichtbar **für den Eltern-Node** |
| `get(port)` | Sucht in `_local` → Eltern-Container → ... → Root |
| `has(port)` | Prüft, ob Port in der lokalen Kette existiert |
| `fork()` | Erzeugt Kind-`NodePorts` (siehe Vererbung) |
| `mount(parent)` | Hängt in Eltern-Baum ein (siehe Mounten) |

---

## Vererbungskette: `fork()` und `mount()`

### `fork()` – Kind-Node erbt Capabilities

Wird in `Node.add()` aufgerufen (`node.py:216-217`):

```python
if self.ports:
    child.ports = self.ports.fork()
```

`fork()` erzeugt einen neuen `NodePorts`:

```python
def fork(self) -> NodePorts:
    return NodePorts(
        publish_to=self._local,    # Kind published in Eltern-Lokal
        local=self._local.fork(),  # Kind-Lokal hat Eltern-Lokal als Parent
    )
```

**Effekt:** Kinder sehen alle Capabilities des Eltern-Nodes, können aber eigene ergänzen oder überschreiben (wenn `allow_override=True`).

### `mount()` – Subtrees einhängen

Wird in `Node.mount()` und im Runtime-Wiring verwendet:

```python
def mount(self, parent: NodePorts) -> None:
    self._local.mount(parent._local)   # Lookup in Elternbaum erweitern
    self._publish_to = parent._local   # Publikationen gehen zum Eltern-Lokal
```

**Effekt:** Der gemountete Tree behält seine interne Hierarchie, erweitert aber sein Lookup in den Elternbaum. Publikationen gehen direkt in den Eltern-Lokal-Container.

---

## Der Wiring-Prozess

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/wire/runtime.py:146-154`

Alle Plattform-Dienste werden als Ports auf dem **Root-Node** registriert:

```python
platform.ports.provide(OnSourceRead, ds.read)
platform.ports.provide(OnSessionSave, session_manager.save)
platform.ports.provide(OnAuthorizeRead, perm_checker.can_read)
platform.ports.provide(OnAuthorizeWrite, perm_checker.can_write)
platform.ports.provide(OnProjectionResolve, projector.project)
platform.ports.provide(OnResourceLoad, package_reader.get_text)
platform.ports.provide(OnJinjaRender, jinja_engine.render_str)
platform.ports.provide(OnCompile, compiler.compile)
platform.ports.provide(OnErrorResolve, error_resolve)
```

Danach werden alle `Nodes` (Spaces) via `platform.mount(node)` an den Root gehängt → **jeder Node sieht automatisch alle Plattform-Ports via Hierarchie-Lookup**.

---

## Konsum in den Nodes

Jeder Command-Handler bekommt `space: NodeSpace` übergeben. Über `space.ports.get(PortType)` werden benötigte Dienste abgefragt:

### Einfaches Beispiel: `version`-Kommando

**Datei:** `spaces/y5nspace-runtime/src/y5nspace/runtime/runtime/version.py`

```python
async def run(space: NodeSpace):
    projection = await space.ports.get(OnProject)(
        name="version/list",
        lang=space.session.lang,
        state={...},
    )
    yield out(projection)
```

Der Handler braucht nur die Projektions-Funktion. Sie wurde vom Runtime-Wiring als `OnProjectionResolve` auf dem Root registriert – der Node sieht sie via Port-Hierarchie.

### Komplexeres Beispiel: `su`-Kommando

**Datei:** `spaces/y5nspace-ident/src/y5nspace/ident/runtime/su.py`

```python
async def run(space: NodeSpace):
    namespaces = space.ports.get(Namespaces)
    resolver = space.ports.get(PermissionResolver)
    on_authenticate = space.ports.get(OnAuthenticate)
    on_save_session = space.ports.get(OnSessionSave)
    on_project = space.ports.get(OnProject)
    ...
```

Hier werden mehrere Ports gleichzeitig benötigt:
- `Namespaces` → vom Ident-Space selbst bereitgestellt (`provide`)
- `OnAuthenticate` → vom Ident-Space bereitgestellt
- `OnSessionSave` → vom Runtime-Wiring auf Root bereitgestellt
- `OnProject` → vom Runtime-Wiring auf Root bereitgestellt
- `PermissionResolver` → vom Ident-Space bereitgestellt

---

## Ports als Protokolle

Ports sind **Protokolle** (keine konkreten Typen) – das ermöglicht loses Koppeln:

```python
# spaces/y5nspace-ident/src/y5nspace/ident/ports.py
class OnProject(Protocol):
    async def __call__(
        self, *, name: str, lang: str, state: dict
    ) -> Projection: ...
```

Das Binding erfolgt rein **strukturell** – die registrierte Funktion muss nur dem Protokoll entsprechen. **Kein Registrierungsdekorator, keine Magic, kein Interface-Registry.** `Container.bind()` prüft nur, ob es eine Instanz ist (keine Klasse), aber nicht den Typ.

---

## Zusammenfassung

| Konzept | Bedeutung |
|---------|-----------|
| `Container` | Hierarchischer DI-Container mit Eltern-Kette |
| `NodePorts` | Kapselt zwei Container: lokal (nach unten vererbt) + publish (nach oben) |
| `provide(port, cap)` | Macht Capability lokal + für Kinder verfügbar |
| `publish(port, cap)` | Exportiert Capability zum Eltern-Node |
| `get(port)` | Holt Capability aus lokaler Kette (Node → Eltern → ... → Root) |
| `fork()` | Erzeugt Kind-Scope: Kind sieht alles vom Eltern-Node, kann ergänzen |
| `mount(parent)` | Hängt kompletten Subtree ein, erweitert Lookup in Elternbaum |
| `On*`-Protokolle | Typisierte Port-Definitionen als `Protocol`-Klassen (strukturelles Typing) |

### Datenfluss-Diagramm

```
Root-Node (Platform)
  _local: [OnProjectionResolve, OnSourceRead, OnSessionSave, ...]
  |
  mount() → Ident-Space
  |   _local: [Namespaces, UserService, GroupService, ...]
  |   _local.parent → Root._local  (sieht Plattform-Ports)
  |   |
  |   add() → "su"-Node
  |       _local: []  (leer, aber geerbt von Ident-Space)
  |       _local.parent → Ident-Space._local
  |       _local.parent.parent → Root._local
  |
  mount() → Shell-Space
      _local: [...]
      _local.parent → Root._local
```

Ein `get(OnProject)` im `su`-Node wandert:
1. `su-Node._local` → nicht gefunden
2. `Ident-Space._local` → nicht gefunden
3. `Root._local` → **gefunden** (wurde dort per `provide` registriert)

---

## Capability System vs. Dependency Injection

Die Implementierung verwendet DI-Mechanik (`Container.bind/get`, Eltern-Kette). Der **Entwurf** ist jedoch ein Capability System.

### Was spricht für Capability System?

**1. Zwei Richtungen (`provide` vs `publish`)**

Echtes DI kennt nur Container, Konsumenten ziehen sich raus. `NodePorts` hat zwei explizite Richtungen:

```python
def provide(self, port, capability):
    self._local.bind(port, capability)  # ↓ delegiert nach unten (für Kinder)

def publish(self, port, capability):
    self._publish_to.bind(port, capability)  # ↑ exportiert nach oben (für Eltern)
```

`provide` **delegiert Autorität** nach unten – ein Node gibt Kindern bewusst eine Fähigkeit.
`publish` **exportiert Autorität** nach oben – ein Node macht dem Eltern-Node etwas zugänglich.
Das ist keine reine Dependency-Versorgung mehr, sondern **explizite Autoritätsweitergabe** mit Richtung.

**2. `fork()` erzeugt Autoritätsgrenzen, nicht nur Scopes**

```python
def fork(self) -> NodePorts:
    return NodePorts(
        publish_to=self._local,    # Kind published in Eltern-Lokal
        local=self._local.fork(),  # Kind sieht Eltern-Lokal als Parent
    )
```

Jedes `fork()` zieht eine Grenze: Das Kind sieht via Lookup zwar Eltern-Caps, aber `publish()` schreibt gezielt in den Eltern-Container. Es geht nicht um Bequemlichkeit, sondern um **wer darf was wohin exportieren**. In DI wäre das einfach `child = parent.fork()` – flach, ohne Richtung.

**3. `mount()` etabliert Vertrauenszonen**

```python
def mount(self, parent: NodePorts) -> None:
    self._local.mount(parent._local)    # Lookup erweitern
    self._publish_to = parent._local    # Publikationen umleiten
```

Ein gemounteter Subtree (z.B. `y5nspace-ident`) behält seine interne Autoritätsstruktur, bekommt aber Lookup-Zugriff auf den Elternbaum. **Der Subtree bleibt autonom** – er entscheidet selbst, welche internen Capabilities er per `publish()` nach oben gibt. Das ist **Principle of Least Authority** (POLA).

**4. Kein globaler Container, keine Ambient Authority**

In klassischem DI gibt es meist einen Root-Container mit Ambient Authority: *jeder* Service ist *überall* verfügbar. In Yakoon gibt es zwar einen Root, aber:
- Nicht alle Ports sind auf Root registriert – viele sind tief in Spaces (`Namespaces`, `UserService`, `GroupService`)
- Ein Node im `ident`-Space sieht Root-Ports (Projektion, SourceRead), aber nicht die internen Ports des `runtime`-Spaces
- **Sichtbarkeit ist eine Frage der Hierarchieposition**, nicht der Registrierung

### Konzeptuelle Unterschiede

| Aspekt | Dependency Injection | Capability System |
|--------|-------------------|-------------------|
| **Grundfrage** | "Was braucht dieser Code?" | "Was darf dieser Code tun?" |
| **Autorität** | Ambient (alles im Container ist verfügbar) | Transferiert (explizit weitergereicht) |
| **Richtung** | Meist top-down oder zentral | Explizit: provide ↓, publish ↑ |
| **Granularität** | Ganze Dienste | Einzelne berechtigte Operationen |
| **Grenzen** | Logische Paketgrenzen (import) | Hierarchische Autoritätsgrenzen (fork/mount) |
| **Sicherheit** | Nachträglich (Auth-Checks in Methoden) | Eingebaut (was du nicht hast, kannst du nicht rufen) |
| **Metapher** | "Hole dir was du brauchst" | "Hier ist genau das, wofür du autorisiert bist" |

### Fazit

DI ist das **Wie** (die technische Umsetzung mit `Container.bind/get`).
Capabilities sind das **Was** (das Architekturkonzept).

`NodePorts` beantwortet nicht die DI-Frage "wie kriege ich meine Abhängigkeiten?", sondern die Capability-Frage **"welche Operationen darf dieser Knoten im Baum ausführen und wem gibt er sie weiter?"** Das ist der Unterschied zwischen einem DI-Framework und einem Capability System.
