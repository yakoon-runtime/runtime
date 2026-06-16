# Flows, Jobs und der Scheduler

## Wie Ausführung und Persistenz im Yakoon-Runtime funktionieren

---

## 1. Was ist ein Flow? (Konzept)

Ein **Flow** ist eine persistente, suspendierbare Ausführungseinheit – die Runtime-Manifestation eines Benutzers, der einen **Node** (ein Kommando) aufruft. Anders als ein einfaches Request/Response kann ein Flow über **mehrere Interaktionen hinweg** leben: er kann Output emittieren, auf Input warten, schlafen, zwischen Vorder- und Hintergrund wechseln und später fortgesetzt werden.

**Metapher:** Ein Flow ist wie ein *Prozess* in einem Betriebssystem. Er hat einen Zustand, einen Ausführungskontext (den Generator-Stack), eine Lebensdauer und kann blockiert, schlafend oder aktiv sein.

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/flow/flow.py`

```python
@dataclass
class Flow:
    id: str                        # UUID-hex (global eindeutig)
    node: Node                     # Der ausgeführte Command-Node
    event: InputEvent              # Das auslösende Eingabe-Event
    cursor: FlowCursor             # Der Generator-Stack (Execution Context)
    control: Control | None        # Aktueller Kontroll-Zustand
    view: Any | None               # Letzte persistierte Projection
    scheduled: bool                # Bereits in der Ready-Queue?
    wake_at: float | None          # Aufwach-Zeitpunkt (für Sleep)
    kind: FlowKind                 # USER (sichtbar) oder SYSTEM (intern)
    pipeline: list[str] | None     # Restliche Pipeline-Kommandos
    inbox: dict[str, deque]        # Per-Channel-Event-Mailbox
```

---

## 2. Das Herzstück: Generator-basierte Ausführung

Der entscheidende architektonische Insight: **Ein Flow ist ein Async-Generator**.

Jeder Node-Handler (`async def run(space)` oder `async def setup(space)`) ist ein **Async-Generator** (`async def` mit `yield`). Der `FlowCursor` verwaltet einen **Stack dieser Generatoren**.

### FlowCursor

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/flow/cursor.py`

```python
class FlowCursor:
    _stack: list[AsyncGenerator]   # Generator-Stack
    handler_name: str              # "run" oder "setup"
```

| Methode | Funktion |
|---------|----------|
| `next(node, ctx)` | Ersten oder nächsten Schritt des Generators ausführen |
| `send(event)` | Generator fortsetzen (nach `AwaitEvent`) |
| `push(gen)` | Subgenerator auf den Stack legen |
| `pop()` | Erschöpften Generator vom Stack nehmen |
| `has_stack()` | Gibt es noch aktive Generatoren? |

Der `cursor.next(node, ctx)`-Aufruf:
1. **Beim ersten Aufruf**: Wrapp den Node-Handler via `_ensure_step()` in einen Async-Generator, legt ihn auf den Stack, ruft `anext(gen)` für den ersten `yield` auf
2. **Bei Folgeaufrufen**: Ruft `anext` auf dem obersten Generator auf
3. **Bei `StopAsyncIteration`**: Pop vom Stack. Wenn Stack leer → Flow ist fertig

### Der Step-Cycle (`CommandEngine.step_flow`)

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/machine/engine.py`

```
1. Normal step: cursor.next(node, ctx) → generator advances one yield
   └─ yield Outcome(control=..., effects=..., value=...)  → normal
   └─ yield InputEvent  → wird in Generator zurückgesendet
   └─ yield async_generator  → push auf Cursor-Stack (Subflow)
   └─ StopAsyncIteration  → Generator erschöpft, pop

2. AwaitEvent step: if flow blocked on AwaitEvent
   └─ Prüft inbox auf Nachrichten
   └─ Wenn Nachricht: pop, clear control, cursor.send(event)
   └─ Wenn keine: return None (flow bleibt blockiert)

3. Outcome processing:
   └─ effects sofort anwenden (emit view, foreground/background, emit event)
   └─ control extrahieren und in flow.control setzen
   └─ Outcome an Scheduler zurückgeben
```

### Der Generator-Wrapper (`_ensure_step`)

Node-Handler können sein:
- **Async-Generator** → direkt verwendbar
- **Coroutine** → wird in Generator gewrapp: `await coro; yield Outcome()`
- **None** → wird in Generator gewrapp: `yield Outcome()`

---

## 3. Control – Was passiert als nächstes?

**Datei:** `runtime/y5ncore-base/src/y5n/base/flow/primitives/control.py`

Controls sind die **Scheduling-Entscheidungen** eines Flows. Sie sagen dem Scheduler: "Was soll mit mir als nächstes passieren?"

```python
class Control:
    blocking: bool          # Blockiert dieser Control den Flow?
    is_runnable(flow)       # Darf der Flow gesterept werden?
    on_enter(flow, scheduler, session)  # Was passiert beim Betreten?
```

| Control | `blocking` | `is_runnable` | `on_enter` | Bedeutung |
|---------|-----------|---------------|------------|-----------|
| **Stop** | `True` | `True` | `session.del_flow(flow)` | Flow beenden |
| **Continue(data)** | `False` | `True` | Nächsten Pipeline-Befehl dispatchen | Pipeline-Verkettung |
| **YieldToScheduler** | `False` | `True` | Flow wieder einreihen (`schedule_flow`) | CPU abgeben, andere Flows lassen |
| **AwaitEvent(channel)** | `True` | nur wenn Mail da | – | Auf Eingabe warten |
| **Suspend** | `True` | `False` | – | Unbegrenzt pausieren (muss extern resumed werden) |
| **Sleep(wake_at)** | `True` | `False` | `schedule_sleep(flow, session, wake_at)` | Bis Zeitpunkt schlafen |
| **SleepUntil(timestamp)** | `True` | `False` | wie Sleep | Bis absolute Zeit schlafen |

### Wake-Mechanismus

Bei `Sleep`/`SleepUntil` wird der Flow in einen **Min-Heap** (`_sleeping`) eingetragen. Der Scheduler prüft bei jedem Zyklus, ob ein Flow aufwachen muss und ruft dann `control.on_wake()` auf → setzt Control auf `YieldToScheduler` und reiht den Flow wieder ein.

---

## 4. Effects – Welche Seiteneffekte treten auf?

**Datei:** `runtime/y5ncore-base/src/y5n/base/flow/primitives/effect.py`

Effects beschreiben **Seiteneffekte**, die beim Verarbeiten eines `Outcome` ausgeführt werden. Sie werden sofort von `CommandEngine._apply_effects()` angewandt.

| Effect | Wirkung |
|--------|---------|
| **EmitView(view, persist=False)** | Sendet eine Projection an den Client. Wenn `persist=True`, wird sie in `flow.view` gespeichert (für spätere Foreground-Wiederherstellung) |
| **Foreground(flow_id=None)** | Setzt diesen Flow als aktiven Vordergrund-Flow (`session.set_foreground_flow(id)`) |
| **Background()** | Entfernt diesen Flow aus dem Vordergrund (`session.set_foreground_flow(None)`) |
| **EmitEvent(channel, event)** | Legt ein `InputEvent` in die eigene `inbox[channel]` (für `send()`/`receive()`) |

---

## 5. Outcome – Die Einheit des Fortschritts

**Datei:** `runtime/y5ncore-base/src/y5n/base/flow/primitives/outcome.py`

```python
@dataclass
class Outcome:
    control: Control | None   # WAS PASSIERT ALS NÄCHSTES
    effects: list[Effect]     # SEITENEFFEKTE jetzt ausführen
    value: Any | None         # RÜCKGABEWERT (für Pipelines oder implizites EmitView)
```

Jeder `yield` in einem Handler produziert genau **ein** `Outcome`. Der Scheduler verarbeitet es in `_handle_outcome()`:

```
Outcome empfangen
  → effects sofort anwenden (emit, foreground/background, emit_event)
  → flow.control = outcome.control setzen
  → control.on_enter(flow, scheduler, session) aufrufen
  → control entscheidet über den weiteren Lebenszyklus
```

---

## 6. Das DSL – Die "Physik" der Flow-Interaktion

Handler interagieren mit dem System **ausschliesslich** über DSL-Funktionen. Diese sind im Package `y5n.base.flow` definiert und produzieren `Outcome`-Objekte.

```python
# y5n/api/dsl.py oder y5n/base/flow/__init__.py

async def receive() -> InputEvent:
    """Warte auf Benutzereingabe (blockiert den Flow)."""
    outcome = Outcome(control=AwaitEvent("default"))
    event = yield outcome
    return event

def out(projection) -> Outcome:
    """Sende eine Projection an den Client."""
    return Outcome(effects=[EmitView(projection)])

def prompt(projection) -> Outcome:
    """Sende Projection + werde Vordergrund + warte auf Eingabe."""
    return Outcome(
        effects=[
            EmitView(projection, persist=True),
            Foreground(),
        ],
        control=AwaitEvent("default"),
    )

def send(channel, event) -> Outcome:
    """Sende ein Event in den eigenen Inbox-Kanal."""
    return Outcome(effects=[EmitEvent(channel, event)])

def foreground() -> Outcome:
    """Werde aktiver Vordergrund-Flow."""
    return Outcome(effects=[Foreground()])

def background() -> Outcome:
    """Gib den Vordergrund ab, bleib aber im Hintergrund aktiv."""
    return Outcome(effects=[Background()])

def suspend() -> Outcome:
    """Pausiere unbegrenzt (muss via :fg resumed werden)."""
    return Outcome(control=Suspend())

def delay(seconds) -> Outcome:
    """Schlafe für Sekunden."""
    wake = time.time() + seconds
    return Outcome(control=Sleep(wake))
```

---

## 7. Der Scheduler – Das Herz der Runtime

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/machine/scheduler.py`

Der Scheduler ist eine **Async-Event-Loop**, die Flow-Ausführung verwaltet und dispatched.

### Queues

- `_ready_user`: `deque[(Session, Flow)]` – sichtbare Benutzer-Jobs (`FlowKind.USER`)
- `_ready_system`: `deque[(Session, Flow)]` – interne System-Flows (`FlowKind.SYSTEM`)
- `_sleeping`: `list[(wake_at, Session, Flow)]` – Min-Heap für schlafende Flows

### Budgets (Leistungsbegrenzung)

| Konstante | Wert | Bedeutung |
|-----------|------|-----------|
| `MAX_STEPS_PER_CYCLE` | 20 | Max Schritte pro Scheduler-Zyklus |
| `MAX_TIME_PER_CYCLE` | 10 ms | Max Wanduhrzeit pro Zyklus |
| `MAX_ITERATIONS` | 1000 | Max Flow-Dequeues pro Zyklus (Sicherheitsgrenze) |
| `MAX_STEPS_PER_FLOW` | 10 | Max Schritte pro Flow, bevor er zurückgestellt wird |
| `MAX_TIME_PER_FLOW` | 2 ms | Max Zeit pro Flow, bevor er zurückgestellt wird |

### Hauptschleife (`run()`)

```
while _running:
    1. Schlafende Flows aufwecken (Heap-Durchlauf, on_wake aufrufen)
    2. Wenn keine ready Flows:
         a. Wenn schlafende existieren: auf nächsten Wake-Zeitpunkt warten
         b. Sonst: unbegrenzt auf _event warten
    3. Hauptverarbeitung: solange Flows ready UND Budget nicht erschöpft:
         a. Nächsten Flow holen (System vor User)
         b. Überspringen, wenn control.is_runnable() == False
         c. Steppen: on_step_flow() → CommandEngine.step_flow()
         d. Wenn Outcome zurück: _handle_outcome(outcome)
              - flow.control = outcome.control
              - control.on_enter(flow, scheduler, session)
         e. Refresh: alle Flows mit YieldToScheduler wieder einreihen
         f. Wenn Pro-Flow-Budget erschöpft: Flow zurückstellen, innere Schleife break
    4. Wenn Zyklus-Budget erschöpft: asyncio.sleep(0) (Event-Loop gönnen)
```

### Dispatch (`dispatch()`)

Erzeugt einen neuen Flow aus einem Input-Event:

```python
async def dispatch(self, session, event):
    # → CommandEngine.dispatch() → neues Flow-Objekt
    # → session.add_flow(flow)
    # → schedule_flow(flow, session) → in ready queue
```

### Fehlerbehandlung

Wenn `on_step_flow` eine Exception wirft:
1. Vordergrund-Flow der Session wird entfernt
2. `_show_error()` erzeugt eine Error-Projection via `on_error_resolve`
3. Error wird via `on_show_projection` an den Client gesendet

---

## 8. Der Runner – Input-Router pro Session

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/machine/runner.py`

Der Runner ist der **Input-Router** jeder Session. Er entscheidet, wohin Benutzereingaben gehen:

```python
async def on_input(self, event):
    # 1. Runtime-Kommandos direkt dispatchen
    if event.data in self._runtime_commands:  # z.B. ":bg"
        await self.on_dispatch(session, event)
        return

    # 2. Wenn Vordergrund-Flow existiert: Input in dessen Inbox
    flow = self._session.foreground_flow
    if flow:
        flow.push_event(event)          # in inbox["default"]
        self.on_schedule_flow(flow)     # Scheduler wecken
        return

    # 3. Sonst: neues Kommando dispatchen
    await self.on_dispatch(session, event)
```

Das ist der Mechanismus, der **Flows über mehrere Inputs hinweg leben lässt**: Der Runner leitet Input nicht an einen neuen Befehl, sondern in die Mailbox des wartenden Flows.

---

## 9. Die CommandEngine – Flow-Erzeugung und Dispatch

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/machine/engine.py`

### Dispatch-Prozess (`dispatch()`)

```python
async def dispatch(self, session, event):
    # 1. Input parsen (Tokens, Pipeline extrahieren)
    event, pipeline = self.on_parse_input(event)

    # 2. Node auflösen (Baumdurchlauf)
    node, tokens = self.on_resolve_command(
        parent=session.get_current_node(),
        key=event.data,
        tokens=event.tokens,
        session=session,
    )

    # 3. Guard: Node muss ausführbar sein
    if not node.has_run():
        return None

    # 4. Flow erzeugen
    flow = Flow(
        id=uuid4().hex,
        node=node,
        pipeline=pipeline,
        event=event.update(data=node.key, tokens=tokens),
        cursor=FlowCursor("run"),    # "run"-Handler
        kind=FlowKind.USER,
    )

    # 5. In Session registrieren
    session.add_flow(flow)
    return flow
```

### Setup-Prozess (`setup()`)

```python
async def setup(self, session, node):
    if not node.has_setup():
        return None
    flow = Flow(
        id=uuid4().hex,
        node=node,
        event=InputEvent(node.key, tokens=[]),
        cursor=FlowCursor("setup"),  # "setup"-Handler
        kind=FlowKind.USER,
    )
    session.add_flow(flow)
    return flow
```

---

## 10. Jobs – Der sichtbare Teil der Flows

Ein **Job** ist ein **benutzersichtbarer Flow** (`FlowKind.USER`). Die Begriffe werden in der Benutzerebene synonym verwendet.

### Beziehung Flow ↔ Job

```
Flow (jeder Flow)
├── FlowKind.USER  → Job (in `jobs list` sichtbar)
└── FlowKind.SYSTEM → interner Flow (nicht sichtbar)
```

Die Session hält:
```python
class Session:
    _flows: dict[str, Flow]           # Alle Flows (USER + SYSTEM)
    _foreground_flow_id: str | None   # Aktiver Vordergrund-Flow
```

### Jobs Space-Befehle

**Datei:** `spaces/y5nspace-runtime/src/y5nspace/runtime/runtime/jobs/`

| Befehl | Funktion |
|--------|----------|
| `jobs` (default) | Listet alle aktiven Jobs mit Index, Label und Status |
| `jobs list` | Explizite Liste aller Jobs |
| `jobs stop <n>` | Flow per 1-basiertem Index beenden (`session.del_flow`) |
| `jobs :fg <n>` | Flow per Index in den Vordergrund holen |
| `jobs :bg` | Aktuellen Vordergrund-Flow in den Hintergrund |

`jobs :fg` stellt auch die letzte persistierte Projection wieder her (`flow.view`) und weckt suspendierte Flows auf (`control.resume()`).

---

## 11. Das Konzept: Wie Jobs über Inputs hinweg persistieren

Der entscheidende Mechanismus, der Hintergrund-Jobs ermöglicht:

```
zeit:  t1          t2          t3          t4          t5
       │           │           │           │           │
Flow:  [----läuft----|----wartet----|----läuft----|----Stop]
                     ↑             ↑
               User tippt      User tippt
               "Hallo"         "Welt"
               Runner leitet   Runner leitet
               in flow.inbox   in flow.inbox
```

### Was passiert Schritt für Schritt:

1. **Flow-Erzeugung** (t1): User tippt `receive`. `Scheduler.dispatch()` erzeugt einen Flow mit `FlowCursor("run")`. Der Generator startet.

2. **Handler läuft** (t1-t2): Der Handler (`async def run(space)`) führt Code aus und erreicht `yield receive()`. Die DSL-Funktion `receive()` produziert:
   ```python
   Outcome(
       control=AwaitEvent("default"),
       effects=[Foreground()],  # implizit von prompt()
   )
   ```

3. **Flow blockiert** (t2-t3): `CommandEngine` setzt `flow.control = AwaitEvent`. Der Scheduler prüft `is_runnable()` → `False`, weil die Inbox leer ist. Der Flow schlummert in `Session._flows`. **Sein Generator-Stack bleibt erhalten** – der Python-Generator ist bei `yield` pausiert.

4. **Benutzereingabe** (t3): User tippt "Hallo". `Runner.on_input()` sieht einen Vordergrund-Flow und ruft `flow.push_event(event)` auf. Das Event landet in `flow.inbox["default"]`. Der Scheduler wird geweckt.

5. **Flow wird gesterept**: Scheduler prüft `is_runnable()` → `True` (Mail ist da). `CommandEngine._next_step()` sieht `AwaitEvent`, poppt das Event aus der Inbox, löscht das Control und ruft `cursor.send(event)` auf.

6. **Generator erwacht**: Der Python-Generator erhält das Event als Rückgabewert von `yield receive()`:
   ```python
   event = yield Outcome(control=AwaitEvent("default"))
   # event ist jetzt das InputEvent("Hallo")
   ```

7. **Flow läuft weiter** (t3-t4): Handler verarbeitet das Event, macht weitere `yield`s, erreicht irgendwann `yield receive()` → wieder blockiert.

8. **Irgendwann Stop** (t5): Handler erreicht `yield Outcome(control=Stop())`. `Stop.on_enter` ruft `session.del_flow(flow)`. **Flow wird entfernt.**

### Was persistiert den Flow zwischen Inputs?

**Der Python-Generator selbst.** `FlowCursor._stack` hält den aktiven Generator. Ein `await`-basierter Call-Stack würde sich nach jeder Operation auflösen – ein Generator bei `yield` **behält seinen kompletten lokalen Zustand**: lokale Variablen, Ausführungsposition, geöffnete Ressourcen.

Die Kette ist:

```
Flow (Dataclass)
  └─ cursor: FlowCursor
      └─ _stack: [active_generator]  ← PYTHON GENERATOR (bei yield pausiert)
          └─ lokale Variablen erhalten
          └─ Ausführungsposition erhalten
          └─ kann via send() fortgesetzt werden

Session hält:
  └─ _flows: {"id": Flow, ...}  ← Flow existiert, solange Session lebt
  └─ _foreground_flow_id: str    ← bestimmt Input-Routing
```

### Das Konzept in einem Satz:

> **Ein Flow persistiert über den Python-Generator-Mechanismus. Der Generator pausiert bei `yield`, sein lokaler Zustand bleibt erhalten, und `send()` setzt ihn fort. Der Scheduler entscheidet, wann und welcher Generator läuft. Der Runner routet Input in die Inbox des Generators.**

---

## 12. Pipeline-Verkettung

Flows können via `|`-Operator verkettet werden:

```
cmd1 | cmd2 | cmd3
```

Die Pipeline wird beim Parsen erkannt. Der erste Befehl (`cmd1`) bekommt die restlichen als `flow.pipeline = ["cmd2", "cmd3"]`.

Wenn `cmd1` mit `Continue(wert)` endet:
1. `Continue.on_enter` dispatched `cmd2` mit `payload=wert`
2. `cmd2` bekommt `pipeline = ["cmd3"]`
3. Flow wird wieder eingereiht (empfängt dann die Ausgabe von cmd2)

Das ist eine **sequentielle Komposition** von Flows – das Konzept ähnelt UNIX-Pipes, aber die Daten fliessen als `Outcome.value` durch das System, nicht als Stream-Byte.

---

## 13. Zusammenfassung

| Konzept | Bedeutung |
|---------|-----------|
| **Flow** | Persistente, suspendierbare Ausführungseinheit (ein "Prozess") |
| **FlowCursor** | Generator-Stack – der Execution Context eines Flows |
| **Control** | Scheduling-Entscheidung (Stop, AwaitEvent, Sleep, Suspend, ...) |
| **Effect** | Seiteneffekt (EmitView, Foreground, Background, EmitEvent) |
| **Outcome** | Einheit des Fortschritts: Control + Effects + Value |
| **Scheduler** | Async-Event-Loop mit Ready-Queues, Sleeping-Heap, Budgets |
| **Runner** | Input-Router pro Session: leitet Input an Vordergrund-Flow |
| **Job** | Ein benutzersichtbarer Flow (`FlowKind.USER`) |
| **Inbox** | Per-Channel-Mailbox: Events für `AwaitEvent` |
| **Pipeline** | Sequentiell verkettete Flows via `\|` |

### Lebenszyklus eines Flows

```
ERZEUGT → READY → STEPPING → AWAIT_EVENT → READY → STEPPING → STOP
           │          │                        │          │
       schedule   cursor.next()            schedule   cursor.next()
      _ready_q    yield Outcome()         _ready_q    yield Stop()
```

### Das Magische: Warum funktioniert das?

Weil **Python-Generators** ihren Zustand zwischen zwei `yield`s behalten. Kein Framework, keine Magie – nur:

```python
# Handler-Code
async def run(space):
    name = None
    while name is None:
        yield out(space.project("ask_name"))  # Projection senden
        event = yield receive()               # pausieren auf Eingabe
        name = event.text.strip()
    yield out(space.project("hello", {"name": name}))
```

Zwischen `yield receive()` und dem nächsten `yield` kann Stunden später ein Input-Event kommen. Der Generator wartet. Sein lokales `name=None` bleibt erhalten. Der Scheduler verwaltet die Queue. Der Runner routet den Input.
