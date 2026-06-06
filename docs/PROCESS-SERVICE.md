# Process Service – Vorschlag

> Stand: 2026-06-06

---

## 1. Worum es geht

Ein Flow soll Arbeit delegieren können, ohne zu blockieren:

```python
task = yield run_task("generate_pdf", customer_id=123)
result = yield receive(f"task:{task.id}")
yield out_text(f"PDF erzeugt: {result}")
```

Der Task läuft als **OS-Prozess** (subprocess). Der Flow wartet per Event.

---

## 2. Primitive

### `run_task(command, **kwargs)`

Neues DSL-Primitive in `y5n/base/flow/dsl.py`:

```python
@dataclass
class RunTask:
    command: str
    kwargs: dict[str, Any]
    task_id: str = ""
```

- `command` – Name einer registrierten Task-Funktion oder Binärname
- `kwargs` – Parameter für die Task
- Rückgabe: `RunTaskResult(task_id, channel)`

Das Outcome enthält:

```python
@dataclass
class RunTaskResult:
    task_id: str
    channel: str  # z. B. "task:a1b2c3"
```

Der Flow macht dann:

```python
result = yield receive(task.channel)
```

---

## 3. Process Service

Neuer Service in der Runtime:

```python
class ProcessService:
    async def start(self, command: str, kwargs: dict) -> TaskHandle: ...
    async def kill(self, task_id: str) -> None: ...
    def status(self, task_id: str) -> TaskStatus: ...
    def list(self) -> list[TaskInfo]: ...
```

**TaskHandle:**

```python
@dataclass
class TaskHandle:
    task_id: str
    channel: str
    pid: int
```

### 3.1 Task-Arten

Zwei Kategorien:

**Built-in Tasks** – registrierte Python-Funktionen:

```python
@runtime.task("generate_pdf")
async def generate_pdf(customer_id: int) -> bytes:
    ...
```

**OS-Prozesse** – beliebige Binaries:

```python
task = yield run_task("pdflatex", args=["document.tex"])
task = yield run_task("python", script="scripts/hello.py")
```

Die Unterscheidung passiert im Process Service:
1. Ist `command` als Built-in registriert? → Aufruf
2. Sonst: `subprocess.Popen(command, **kwargs)`

### 3.2 Kommunikation

Der Task kommuniziert sein Ergebnis per **Event** zurück:

```python
emit(Event(f"task:{task_id}", result))
```

Für OS-Prozesse gibt es zwei Wege:

- **stdout/returncode** – wird vom Process Service abgefangen und als Event gesendet
- **Strukturierte Ausgabe** – Task schreibt JSON nach stdout → Process Service parsed und sendet als Event

### 3.3 Lifecycle

```
Flow                           Process Service                OS Process
────                           ───────────────                ──────────
yield run_task("sleep", n=5) ─→ start(command, kwargs)
                                   │                            starten
                                   └── task_id, pid ──────────→ läuft
← task_id, channel
yield receive(channel) ───────→ suspend (AwaitEvent)
                                                                fertig
                                   send(task:channel, done) ←── exit
                              ───→ Flow resume
← result
```

---

## 4. Erster Test

Minimaler Testfall, der zeigt, dass die Kette funktioniert:

```python
async def run(_):
    task = yield run_task("sleep", seconds=3)
    yield out_text(f"Task gestartet: {task.task_id}")
    result = yield receive(task.channel)
    yield out_text(f"Task beendet: {result}")
```

Dafür brauchen wir:

1. `RunTask`-Outcome in `dsl.py`
2. `ProcessService` mit `start(kommt, kwargs)`
3. Built-in `sleep`-Task (einfach `asyncio.sleep(n)` + Event senden)
4. `Spawn`-Handler im Runner, der `ProcessService.start()` aufruft

Das ist vermutlich der kürzeste Weg, um die Kette

```text
Flow → Process Service → OS Process → Event → Flow
```

durchgehend zu testen.

---

## 5. Abgrenzung

**Nicht Teil dieses Vorschlags:**

- Spawn/Join für Flow-startet-Flow (kommt später, wenn nötig)
- Job-Tree in der Projection (UI-Sache)
- Process-Registry (einfach `@runtime.task`-Dekorator reicht)
- Resource-Limits (cgroups, Docker – später)
- Task-Networking (Tasks auf anderen Maschinen – viel später)

---

## 6. Offene Fragen

- Soll `run_task` den Flow automatisch suspendieren, oder muss der Flow explizit `receive` machen? (Der Vorschlag oben nimmt Letzteres – der Flow kriegt sofort die task_id und entscheidet selbst, wann er wartet.)
- Timeout für Tasks?
- Cancel: `yield kill(task.task_id)`?
- Wie findet der Process Service den passenden EventBus, um das Ergebnis-Event zu senden?
