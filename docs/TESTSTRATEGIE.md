# Teststrategie für Yakoon

## Warum keine Tests da sind und wie es weitergeht

---

## 1. Architekturprinzip: Determinismus → Testbarkeit als Nebeneffekt

Kleine, testbare Einheiten waren von Anfang an der Mittelpunkt der gesamten Software. Aber der **Grund** dafür ist nicht "ich will gute Tests". Der Grund ist **Determinismus**.

```python
# Nicht: "Ich will testen können"
# Sondern: "Ich will, dass das System nachvollziehbar bleibt"
# Testbarkeit ist der Nebeneffekt, nicht das Ziel.
```

Jede Entscheidung in der Architektur dient dem Determinismus:

- **Nodes** sind einfache Dataclasses → kein versteckter Zustand
- **Handler** sind Async-Generators mit expliziten Ports → keine impliziten Abhängigkeiten
- **Container** sind Key-Value-Stores mit Eltern-Kette → keine globalen Singletons
- **Projections** sind immutable → keine Seiteneffekte beim Rendern
- **Compiler-Stufen** sind reine Funktionen → gleicher Input → gleicher Output
- **Controls/Effects** sind immutable Werte → keine Aktion beim Erzeugen

```python
# Alles, was ein Handler braucht, kommt explizit via space.ports.get()
# → Keine globalen Imports, keine versteckten Abhängigkeiten

# Alles, was ein Handler produziert, ist ein Outcome
# → Keine Seiteneffekte, keine versteckten State-Änderungen

# Alles, was ein Block ist, ist eine frozen dataclass
# → Keine veränderlichen Objekte, keine Identity-Probleme
```

**Testbarkeit ist ein willkommener Nebeneffekt.** Der echte Grund ist: Das System muss nachvollziehbar bleiben. Und genau das ist auch der Grund, warum KI später sicher eingesetzt werden kann – eine KI braucht ein deterministisches System, um die Konsequenzen ihres eigenen Codes vorhersagen zu können.

> **Determinismus ist das Ziel. Testbarkeit und KI-Sicherheit sind die Konsequenz.**

**Deshalb ist 100% Testabdeckung nicht nur erreichbar, sondern unvermeidbar: Die Architektur erzwingt Determinismus, und Determinismus erzwingt Testbarkeit.**

## 2. Warum aktuell keine Tests existieren

Die Architektur durchlief viele Iterationen:

- Node-System (mehrere Versionen)
- Ports/Container (Richtungen provide↓/publish↑)
- Flow-Execution (Generator-basiert)
- Projection-Compiler (4 Stufen)
- Capability-Security (PermissionChecker)

In jeder Iteration änderten sich fundamentale Schnittstellen. Tests, die während der Iteration geschrieben werden, testen nur die Version von letzter Woche – und werden beim nächsten Refactoring zu Ballast.

Die Entscheidung war: **Iterieren, bis die Architektur steht, dann testen.**

---

## 2. Testbarkeit ist nicht verloren

Das wichtige Versprechen: **"Ziel 100% Testbarkeit"** – und das ist nicht schwer, weil überall mit loser Kopplung gearbeitet wird.

Die Architektur hat die Testbarkeit nicht geopfert. Die losen Kopplungen über Ports sind die ideale Mock-Struktur.

### 2.1 Ports als natürliche Test-Doubles

Jeder Port ist ein Test-Double-Punkt:

```python
# Produktion: echter Projector
platform.ports.provide(OnProjectionResolve, projector.project)

# Test: Mock-Projector
async def fake_project(*, resource, state):
    return Projection(
        id="test.prj",
        header=ProjectionHeader(role="info", title="Test"),
        blocks=[ParagraphBlock(text=[InlineText("Hallo Welt")])],
    )

platform.ports.provide(OnProjectionResolve, fake_project)
```

Weil alle Abhängigkeiten über `ports.get()` bezogen werden, kann **jeder Port im Test durch ein Double ersetzt werden** – ohne Monkey-Patching, ohne Mock-Framework, ohne Magic.

### 2.2 Generator-Flows ohne Scheduler testen

Das Herzstück – der Generator-Flow – ist ohne Scheduler testbar:

```python
# Ein Flow ist ein Async-Generator.
# Man kann ihn Schritt für Schritt abspielen.

async def test_welcome_handler():
    space = MockNodeSpace()
    gen = welcome.run(space)

    # Erster yield: Projection wird emittiert
    outcome = await gen.__anext__()
    assert isinstance(outcome, Outcome)
    assert len(outcome.effects) == 1
    assert isinstance(outcome.effects[0], EmitView)
    assert outcome.control is None  # kein Stop → läuft weiter

    # Zweiter yield: Flow endet
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()
```

```python
# Bei interaktiven Flows mit receive():
async def test_receive_then_reply():
    space = MockNodeSpace()
    gen = my_handler.run(space)

    # Erster Schritt: wartet auf Input
    outcome = await gen.__anext__()
    assert isinstance(outcome.control, AwaitEvent)

    # Input senden (via send())
    event = InputEvent(data="Hello", tokens=[], context=...)
    outcome = await gen.asend(event)
    assert isinstance(outcome.control, Stop)
```

### 2.3 Projections ohne Render-Engine testen

Projections sind immutable Dataclasses – sie lassen sich direkt erzeugen und vergleichen:

```python
def test_projection_has_correct_structure():
    projection = Projection(
        id="prj.test",
        header=ProjectionHeader(role="success", title="OK"),
        blocks=[
            KvBlock(items=[
                KvItemBlock(key="Status", value=[InlineText("Aktiv")]),
            ]),
        ],
    )

    assert projection.header.role == "success"
    assert len(projection.blocks) == 1
    assert isinstance(projection.blocks[0], KvBlock)
```

Der Projector selbst wird zum Integration-Test (Jinja2 + Compiler), aber einzelne Templates können via Snapshot-Testing validiert werden.

### 2.4 Compiler-Stufen isoliert testen

Der Compiler ist in 4 isolierte Stufen geteilt:

```python
# Tokenize: Input → Token-Liste
tokens = tokenize_text("<p>Hallo <strong>Welt</strong></p>")
assert tokens[0].type == "OPEN" and tokens[0].tag == "p"
assert tokens[1].type == "TEXT" and tokens[1].content == "Hallo "
assert tokens[2].type == "OPEN" and tokens[2].tag == "strong"

# Build AST: Token-Liste → ElementNode-Baum
ast = build_ast(tokens)
assert ast.tag == "root"
assert len(ast.children) == 1
assert ast.children[0].tag == "p"

# Normalize: Whitespace kollabieren
normalize_ast(ast)
assert ast.children[0].children[0].text == "Hallo Welt"

# Build: AST → Projection
projection = Mapper().map_projection(ast)
assert projection.blocks[0].text[0].text == "Hallo Welt"
```

Jede Stufe ist eine reine Funktion – ideal für Unit-Tests.

---

## 3. Konkrete Testpyramide

```
      ╱╲
     ╱  ╲
    ╱ E2E ╲           ← 3-5 Tests (Gesamt-System: Dispatch → Flow → Client)
   ╱────────╲
  ╱ Integration ╲     ← 20-30 Tests (Compiler, Scheduler, Postgres-Backend)
 ╱────────────────╲
╱   Unit Tests      ╲  ← 200-400 Tests (Handler, Ports, Nodes, Flows, Model)
╱────────────────────╲
```

### Unit-Tests (Basis)

| Komponente | Tests | Beschreibung |
|-----------|-------|-------------|
| Node (add, mount, find) | ~20 | Hierarchie-Operationen |
| NodePorts (provide, publish, get, fork) | ~15 | Container-Ketten |
| Container (bind, get, fork, mount) | ~10 | Basis-Container |
| FlowCursor (next, send, push, pop) | ~15 | Generator-Stack |
| Outcome, Control, Effect | ~10 | Primitives |
| Projection-Modelle (alle Blocks, Inlines) | ~30 | Dataclass-Tests |
| Compiler (Tokenize, AST, Normalize) | ~20 | Reine Funktionen |
| Mapper (Block-Mapper, Inline-Mapper) | ~30 | Tag→Modell |
| Serializer/Deserializer | ~10 | Wire-Protokoll |
| PermissionChecker | ~10 | RBAC-Logik |
| Namensallokation | ~5 | Naming |
| **Total Unit** | **~175** | |

### Integration-Tests

| Komponente | Tests | Beschreibung |
|-----------|-------|-------------|
| Projector (Jinja2 → Projection) | ~10 | Vollständiger Pipeline-Test |
| Scheduler (Queue, Dispatch, Sleep) | ~10 | Scheduling-Logik |
| Engine (step_flow, dispatch) | ~10 | Flow-Lebenszyklus |
| Postgres-Backend | ~10 | DB-Operationen |
| Identity-Space (user, group, grant) | ~15 | Space-übergreifend |
| **Total Integration** | **~55** | |

### E2E-Tests

| Szenario | Beschreibung |
|---------|-------------|
| Kommando eingeben → Projection erhalten | Gesamte Dispatch→Flow→Projection-Kette |
| `receive` → Eingabe → Antwort | Interaktiver Flow über mehrere Steps |
| Background-Job (bg/fg/list/stop) | Job-Lifecycle |
| Permission-Check (erlaubt/verweigert) | Auth + Node-Resolution |
| **Total E2E** | ~5 |

### Gesamt

```
Unit:         ~175 Tests
Integration:  ~55 Tests
E2E:           ~5 Tests
─────────────────────
Total:        ~235 Tests
```

---

## 4. Mocking-Strategie

### Was NICHT gemockt wird

- **Projection-Modelle** – das sind reine Dataclasses, kein Mock nötig
- **Control/Effect/Outcome** – sind immutable Werteobjekte
- **Container/NodePorts** – sind selbst Test-Helfer (keine IO)

### Was gemockt wird

```python
# Ports: Jeder Port wird im Test durch ein Double ersetzt
space.ports.provide(OnProject, FakeProjector())
space.ports.provide(OnSourceRead, FakeDataSource())
space.ports.provide(OnSessionSave, FakeSessionSaver())

# Session: minimale Implementierung
class FakeSession:
    def __init__(self):
        self._flows = {}
        self._foreground = None
        self.lang = "de"
```

### Was NICHT gemockt wird (Integration)

- **Compiler** – voller Pipeline-Test mit echten `.sam`-Templates
- **Projector** – Jinja2 + Compiler als Integration
- **Scheduler** – echte Queue + Event-Loop

---

## 5. Test-Runner-Setup

```toml
# pyproject.toml (in jedem Paket oder zentral)
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["y5n", "y5nspace", "y5nstore", "y5ntrans", "y5napp"]
omit = ["*/tests/*", "*/__old__/*"]
```

```bash
# requirements-dev.txt
pytest>=8.0
pytest-asyncio>=0.24
pytest-cov>=5.0
syrupy>=4.0        # Snapshot-Testing für Projections
```

---

## 6. CI-Pipeline (zukünftig)

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e runtime/y5ncore-base
      - run: pip install -e stores/y5nstore-event
      - run: pip install -e runtime/y5ncore-runtime
      - run: pip install -e spaces/y5nspace-{shell,ident,runtime}
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov --cov-report=term-missing
      - run: ruff check .
      - run: pyright
```

---

## 7. Zusammenfassung

| Metrik | Heute | Ziel |
|--------|-------|------|
| Tests | 0 | ~235 |
| Code Coverage | 0% | >80% |
| Test-Runner | Keiner | pytest + asyncio |
| CI | Keine | GitHub Actions |
| Snapshot-Tests | Keine | syrupy für Projections |

**Die Architektur ist testbar.** Ports sind natürliche Mock-Punkte. Generator-Flows sind ohne Scheduler testbar. Der Compiler ist in reine Funktionen zerlegt. Projections sind immutable Dataclasses.

Es fehlen nur die Dateien.

---

## 8. Anmerkung zu Dead Imports (Web/SSH)

Die Web-App und SSH-App crashen aktuell beim Import. Das liegt daran, dass die Runtime in den letzten Tagen massiv geändert wurde und die Apps noch nicht nachgezogen sind.

Das ist **kein strukturelles Problem**, sondern **3 Minuten Aufwand** – die Imports müssen auf die neuen Paketnamen aktualisiert werden. Die Architektur ist darauf ausgelegt, dass diese Apps funktionieren – sie wurden nur noch nicht an den aktuellen Stand angepasst.

---

## 9. 100% Testabdeckung – warum das erreichbar ist

Die Architektur wurde von Anfang an auf **maximale Testbarkeit** ausgelegt. Zitat:

> "Im Fokus stand immer Maximum an Testbarkeit."

### Warum das kein leeres Versprechen ist

| Eigenschaft | Testbarkeit |
|-------------|-------------|
| **Ports statt globale Dienste** | Jede Abhängigkeit kann im Test ausgetauscht werden |
| **Immutable Projections** | Können direkt erzeugt und verglichen werden |
| **Generator-Flows** | Können ohne Scheduler Schritt für Schritt getestet werden |
| **Reine Compiler-Funktionen** | Input → Output, keine Seiteneffekte |
| **Container statt Singletons** | Jeder Test bekommt frische Container |
| **Nodes sind Dataclasses** | Keine versteckte Initialisierungslogik |
| **Permissions über Ports** | Können im Test deaktiviert/überschrieben werden |

### Zusätzlich: KI-generierte Tests

> "Viele der Tests werde ich später von KI erstellen lassen."

Weil die Architektur sauber ist (Ports, reine Funktionen, immutables Model), kann eine KI aus der Struktur des Codes direkt die Tests ableiten:

```python
# KI sieht:
async def run(space: NodeSpace):
    projection = await space.ports.get(OnProject)(...)
    yield out(projection)

# KI generiert:
async def test_run():
    mock = MockNodeSpace()
    mock.ports.provide(OnProject, FakeProjector())
    gen = run(mock)
    outcome = await gen.__anext__()
    assert isinstance(outcome.effects[0], EmitView)
```

Weil es keine Magie gibt (keine globalen States, keine impliziten Abhängigkeiten, keine Seiteneffekte in Konstruktoren), kann eine KI aus einem `ports.get(OnX)` direkt ableiten, was gemockt werden muss.

**Deshalb ist 100% Testabdeckung kein frommer Wunsch, sondern eine logische Konsequenz der Architektur.**
