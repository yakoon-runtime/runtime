# Scheduler-Leistungsfähigkeit & Multi-Process-Zukunft

## Analyse des aktuellen Single-Process-Schedulers und der Weg zur Skalierung

---

## 1. Aktuelle Architektur (Single Process)

```
RuntimeHost
  └── Scheduler (async event loop)
      ├── _ready_user: deque[(Session, Flow)]
      ├── _ready_system: deque[(Session, Flow)]
      ├── _sleeping: list[(wake_at, Session, Flow)]   ← Min-Heap
      └── run():
           1. Schlafende Flows wecken
           2. Flow aus Queue holen (System priorisiert)
           3. flow.control.is_runnable() prüfen
           4. CommandEngine.step_flow() → Generator einen Schritt
           5. outcome.control.on_enter() (Stop/AwaitEvent/Sleep/...)
           6. YieldToScheduler-Flows wieder einreihen
           7. Budget check → asyncio.sleep(0)
```

**Ein Prozess. Eine Event-Loop. Kooperatives Multitasking.**

### 1.1 Stärken

| Eigenschaft | Bewertung |
|-------------|-----------|
| **Einfachheit** | ~330 Zeilen, keine Locks, keine IPC |
| **Fairness** | Per-Flow-Budget (10 Steps / 2ms), Per-Cycle-Budget (20 Steps / 10ms) |
| **Priorisierung** | System-Flows vor User-Flows |
| **Schlaf-Mechanismus** | Min-Heap + `asyncio.wait_for` → kein aktives Polling |
| **Fehlerisolierung** | Exception in einem Flow killt nur diesen, nicht den Scheduler |
| **Generator-basiert** | Kein Stack-Frame-Overhead, Zustand ist implizit |

### 1.2 Grenzen

| Grenze | Problem |
|--------|---------|
| **Ein CPU-Kern** | GIL + Event-Loop = ein Kern. CPU-intensive Handler blockieren alle anderen Flows |
| **Kein Failover** | Generator-Zustand ist im RAM. Prozess-Crash → alle Flows verloren |
| **Session-Affinity** | Alle Flows einer Session im selben Scheduler |
| **Keine horizontale Skalierung** | Mehr Traffic → grössere Instanz, nicht mehrere Instanzen |
| **Shared-Nothing** | Node-Baum, Session-Objekt, Ports sind nicht geteilt |

### 1.3 Aktuelle Leistungsgrenze

```python
# Budgets (konservativ eingestellt)
MAX_STEPS_PER_CYCLE = 20          # 20 Schritte pro Zyklus
MAX_TIME_PER_CYCLE = 0.01         # 10 ms pro Zyklus
MAX_STEPS_PER_FLOW = 10           # 10 Schritte pro Flow
MAX_TIME_PER_FLOW = 0.002         # 2 ms pro Flow
```

**Annahme:** Ein `step_flow()` ist meist ein `yield` – das ist im Nanosekunden-Bereich, kein I/O. Nur wenn eine Projection gerendert wird (`await projector.project()`), gibt es I/O (Template laden, Compiler).

**Geschätzte Kapazität bei reinen I/O-Flows:**

```
Pro Zyklus:     20 Flows gesteppt
Pro Sekunde:    ~2000 Flows (bei 10ms/Zyklus + Event-Loop-Pausen)
Pro Session:    10-100 gleichzeitige Flows
Gleichzeitige Sessions: 100-200 (je nach Flow-Dichte)
```

Das ist für ein Team oder einen kleinen Betrieb völlig ausreichend.

---

## 2. Die Flaschenhälse

### 2.1 Generator-Zustand ist nicht serialisierbar

```python
class FlowCursor:
    _stack: list[AsyncGenerator]  # ← Python-Generator-Objekte
```

Das ist der **zentrale Flaschenhals für Multi-Process**:
- Generatoren lassen sich nicht picklen
- Ein Generator bei `yield` kann nicht eingefroren und auf einem anderen Prozess fortgesetzt werden
- Workaround müsste den Python-Generator in eine serialisierbare Zustandsmaschine übersetzen

### 2.2 Session-Objekt ist nicht geteilt

```python
class Session:
    _flows: dict[str, Flow]         # In-Memory
    _foreground_flow_id: str | None # In-Memory
```

Sessions sind in-Memory-Objekte. Zwei Prozesse können nicht denselben `_foreground_flow_id` lesen/schreiben.

### 2.3 Node-Baum ist nicht geteilt

Der Node-Baum (`platform`) ist ein Python-Objekt mit `parent`/`children`-Referenzen. Zwei Prozesse müssten entweder denselben Baum teilen (Shared Memory) oder jeder eine Kopie haben.

---

## 3. Multi-Process-Architekturen

### Option A: Sharded Sessions (einfach)

```
Load Balancer (nach session_key)
  │
  ├── Worker 1: Scheduler + Sessions {0..99}
  ├── Worker 2: Scheduler + Sessions {100..199}
  └── Worker 3: Scheduler + Sessions {200..299}
       │
       └── Shared: Postgres-Store, Node-Baum (jeder Worker hat Kopie)
```

**Wie es funktioniert:**
- Jeder Worker startet einen vollständigen Scheduler + Node-Baum
- Der Load Balancer routet Connections per `session_key % N` zum selben Worker
- Der Event-Store (Postgres) wird von allen geteilt
- Der Node-Baum wird beim Start geladen (oder per Watch-Updates synchronisiert)

**Vorteile:**
- Minimaler Umbaubedarf am Scheduler
- Kein Shared Memory, keine IPC
- Jeder Worker ist ein eigenständiger Prozess

**Nachteile:**
- Ungleichmässige Auslastung (einige Sessions haben viele Flows)
- Node-Baum muss auf jedem Worker identisch sein (Deployment-Herausforderung)
- Kein Failover: Wenn Worker stirbt, sind seine Sessions weg

**Aufwand:** ~1 Woche (Connection-Routing, Worker-Management)

```python
# Skizze: Routing
class Router:
    def __init__(self, workers: list[Scheduler]):
        self.workers = workers

    def get_worker(self, session_key: Key) -> Scheduler:
        idx = hash(session_key) % len(self.workers)
        return self.workers[idx]

    async def on_input(self, connection, event):
        worker = self.get_worker(connection.session_key)
        await worker.receive_input(connection, event)
```

### Option B: Flow Workers (fortgeschritten)

```
Dispatcher
  │
  ├── Worker 1: Scheduler (Flows A-F)
  ├── Worker 2: Scheduler (Flows G-L)
  └── Worker 3: Scheduler (Flows M-Z)
       │
       └── Shared: Session-Store (Redis/Postgres)
                   Node-Baum (jeder Worker hat Kopie)
```

**Wie es funktioniert:**
- Der Dispatcher nimmt InputEvents entgegen und routet sie zum Worker, der den zugehörigen Flow hält
- Jeder Worker hat einen vollständigen Scheduler
- Flows sind an Worker gebunden (nicht an Sessions)
- Session-Data (Permissions, Preferences) liegt in Redis/Postgres

**Vorteile:**
- Bessere Lastverteilung als Sharded Sessions
- Flow-Isolation: Ein Worker mit CPU-Last killt nicht alle Sessions

**Nachteile:**
- Routing wird komplexer (Flow-ID → Worker)
- Session muss aus Shared Storage geladen werden
- Immer noch: Generator-Zustand im RAM, kein Failover

**Aufwand:** ~2-3 Wochen (Dispatcher, Flow-Routing, Session-Sharing)

### Option C: Persisted Flows (höchste Skalierung)

```
Load Balancer
  │
  ├── Worker 1 (stateless)     Backend: Postgres
  ├── Worker 2 (stateless)     ┌──────────────────────┐
  └── Worker 3 (stateless)     │ Flows (serialisiert) │
       │                       │ Sessions             │
       │                       │ Node-Baum (Version)  │
       │                       │ Permissions          │
       │                       └──────────────────────┘
       │
       └── Message Queue (NATS / Redis Pub/Sub)
            für broadcasts: Projection → Client
```

**Wie es funktioniert:**
- Flows sind keine Python-Generatoren mehr im RAM
- Jeder Flow-Schritt: `load(flow_id)` → `execute_step()` → `save(flow_id, new_state)` → `emit(effects)`
- Zustand wird im Store serialisiert (EntityStore oder separater Flow-Store)
- Jeder Worker kann jeden Flow bearbeiten (stateless)

**Vorteile:**
- **Horizontale Skalierung**: Einfach mehr Worker starten
- **Failover**: Worker-Crash → kein Verlust (Flow ist persistiert)
- **Rolling Updates**: Worker werden nacheinander ersetzt
- **Lastausgleich**: Perfekt (jeder Step kann auf anderem Worker laufen)

**Nachteile:**
- **Fundamentaler Umbau**: Generator-Konzept muss ersetzt werden
- **Latenz**: Jeder Step braucht einen Store-Read + Write
- **Komplexität**: Versionierung, Optimistic Locking, Recovery

**Aufwand:** ~1-2 Monate (neues Flow-Modell, Serialisierung, Recovery)

---

## 4. Detaillierte Bewertung der Optionen

| Kriterium | A: Sharded Sessions | B: Flow Workers | C: Persisted Flows |
|-----------|--------------------|-----------------|-------------------|
| **Umbauaufwand** | Gering (1 Woche) | Mittel (2-3 Wo) | Hoch (1-2 Mo) |
| **Horizontale Skalierung** | Linear (pro Session) | Linear (pro Flow) | Linear (perfekt) |
| **Failover** | Nein | Nein | Ja |
| **Generator-Verlust** | Nein | Nein | Ja (muss ersetzt werden) |
| **Latenz (pro Step)** | 0 (RAM) | 0 (RAM) | +1-5ms (Store) |
| **Komplexität** | Niedrig | Mittel | Hoch |
| **Rolling Updates** | Nein | Nein | Ja |

### Empfohlener Pfad

```
Phase 1 (sofort):  Sharded Sessions (Option A)
  → Einfach, löst das Kernproblem "mehrere Kerne nutzen"
  → Aufwand: ~1 Woche

Phase 2 (bald):    Persistierte Session-Data in Postgres
  → Session-Failover: Wenn Worker stirbt, neuer Worker lädt Session aus DB
  → Flows sind dann immer noch weg, aber der Benutzer kann neu verbinden

Phase 3 (später):  Persisted Flows (Option C)
  → Generator-Modell durch serialisierbare Zustandsmaschine ersetzen
  → Wahre horizontale Skalierung + Failover
```

---

## 5. Das Generator-Problem für Option C

Der grösste technische Hebel: **Wie ersetzt man den Python-Generator durch eine serialisierbare Zustandsmaschine?**

### Aktuell (Generator)

```python
async def run(space):
    name = yield receive()          # hier pausiert der Generator
    amount = yield receive()        # und hier
    yield out(result(name, amount))
```

### Zukünftig (Persisted Flow)

```python
# Zustand wird im Store persistiert
@dataclass
class FlowState:
    step: int = 0          # current yield point
    name: str | None = None
    amount: int | None = None

async def run(space, state: FlowState):
    match state.step:
        case 0:
            state.step = 1
            state.name = yield receive()
            save(state)           # persistieren
            yield YieldToScheduler  # zurückgeben, anderer Worker kann übernehmen

        case 1:
            state.step = 2
            state.amount = yield receive()
            save(state)

        case 2:
            yield out(result(state.name, state.amount))
            delete(state)
```

### Alternative: DSL-Compiler

Statt die Zustandsmaschine von Hand zu schreiben, könnte ein Compiler aus dem Generator-Code die serialisierbare Form erzeugen:

```python
# Geschrieben als:
async def run(space):
    name = yield receive()
    amount = yield receive()
    yield out(result(name, amount))

# Kompiliert zu serialisierbarer Zustandsmaschine:
FlowDef(
    steps=[
        Step(id=0, yields=AwaitEvent, store=["name"]),
        Step(id=1, yields=AwaitEvent, store=["amount"]),
        Step(id=2, yields=EmitView, fn=result),
    ]
)
```

Das wäre der **Königsweg**: Der Entwickler schreibt Generatoren, aber die Runtime kompiliert sie in serialisierbare Zustandsmaschinen. Ähnlich wie ein Compiler aus async/await eine Zustandsmaschine macht – nur dass sie persistierbar ist.

---

## 6. Was sich nicht ändern muss

Der Scheduler selbst ist für Multi-Process nicht das Problem. Diese Teile können bleiben:

```python
class Scheduler:
    # Budgets und Fairness bleiben
    MAX_STEPS_PER_CYCLE = 20
    MAX_TIME_PER_CYCLE = 0.01

    # Queue-Struktur bleibt (wird nur pro Worker)
    self._ready_user = deque()
    self._ready_system = deque()

    # Sleeping-Mechanismus bleibt
    self._sleeping = []

    # Outcome-Handling bleibt (Control.on_enter)
    await self._handle_outcome(session, flow, outcome)

    # Einzige Änderung: step_flow wird asynchron und holt/speichert Zustand
    # outcome = await self.on_step_flow(flow=flow, session=session)
    # → wird zu:
    # state = await load_flow_state(flow.id)
    # outcome = await execute_step(flow, state)
    # await save_flow_state(flow.id, state)
```

Der Scheduler ist bereits **gut abstrahiert**:
- Er ruft `on_step_flow` auf – was darin passiert, ist ihm egal
- Er ruft `on_show_projection` auf – wohin die Projection geht, ist ihm egal
- Er ruft `control.on_enter` auf – was der Control tut, ist ihm egal

Diese lose Kopplung macht den Umbau auf Multi-Process einfacher.

---

## 7. Zusammenfassung

| Aspekt | Heute (Single Process) | Morgen (Multi-Process) |
|--------|----------------------|----------------------|
| **Prozesse** | 1 | N (sharded sessions) |
| **CPU-Kerne** | 1 | N |
| **Flow-Zustand** | RAM (Generator) | RAM oder Postgres |
| **Failover** | Kein | Phase 1: nein / Phase 3: ja |
| **Session-Data** | RAM (SessionData) | Postgres |
| **Node-Baum** | RAM (geteilt) | RAM (pro Worker Kopie) |
| **Scheduler-Code** | ~330 Zeilen | ~350 Zeilen (+ Routing) |

### Empfehlung

> **Phase 1 (sofort):** Sharded Sessions.
> Jeder Worker hat einen eigenen Scheduler + Node-Baum-Kopie.
> Der Router verteilt Connections per `session_key % N`.
> Aufwand: ~1 Woche. Nutzen: N Kerne.
>
> **Phase 2 (bald):** Session-Persistenz in Postgres.
> SessionData wird bei jedem Update gespeichert.
> Worker-Crash → Session kann auf anderem Worker neu laden.
> Flows sind dann noch weg, aber der Benutzer kann neu verbinden.
>
> **Phase 3 (Vision):** Persisted Flows.
> Generator-Modell durch serialisierbare Zustandsmaschine ersetzen.
> Flow kann auf jedem Worker laufen. Failover + horizontale Skalierung.
> Aufwand: ~1-2 Monate. Nutzen: Unbegrenzte Skalierung + Ausfallsicherheit.

Der Scheduler ist **nicht der Flaschenhals**. Seine lose Kopplung (`on_step_flow`, `on_show_projection`, `control.on_enter`) ist die beste Voraussetzung für Multi-Process. Das eigentliche Problem ist der in-memory Generator-Zustand – und das ist ein Flow-Problem, kein Scheduler-Problem.
