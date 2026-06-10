# Demo-Architektur: LLM → Command → Task → Port

Kein LLM → Shell. Stattdessen:

## Schichten

```
User Input
  ↓
LLM (sieht nur Tool-Namen)
  ↓  "processes"
Command Resolution (start_cmd → dispatch → find_tool)
  ↓
Tool Handler (async generator)
  ↓  start_task("ps", ["aux"], channel=ch)
Port: OnRunProcess
  ↓
OS-Prozess
```

## Tool Registry

```python
tools = ToolRegistry(
    Tool(key="processes",   description="Liste aller laufenden Prozesse",     run=run_processes),
    Tool(key="memory",      description="Aktuelle Speichernutzung",           run=run_memory),
    Tool(key="containers",  description="Laufende Docker-Container",          run=run_containers),
)
```

Jeder `Tool` ist ein `Node(key=..., run=handler)` — dispatch resolved darauf.

## LLM sieht nur Tool-Namen

Prompt:

```
Verfügbare Tools:
  processes  – Liste aller laufenden Prozesse
  memory     – Aktuelle Speichernutzung
  containers – Laufende Docker-Container

Antworte NUR mit dem Tool-Namen.
```

LLM-Response → `start_cmd(LLM-response, channel=ch)`.

## Tool Handler

```python
async def run_processes(ctx):
    yield start_task("ps", channel=ch, args=["aux"])
    result = yield receive(ch, scope=Scope.SESSION)
    yield out_text(result.stdout)
```

## OnRunProcess Port

```python
class OnRunProcess(Protocol):
    async def run(self, command: str, args: list[str]) -> ProcessResult: ...
```

Nur Tool Handler rufen `run` auf. Unregistrierte Shell-Kommandos existieren nicht.

## Demo-Flow

```
User: "zeige mir alle Prozesse"
  → Chat-Flow: yield receive()
  → LLM: generate("Welches Tool passt?") → "processes"
  → Chat-Flow: yield start_cmd("processes", channel=ch)
  → Dispatch resolviert auf Tool-Node "processes"
  → Sub-Flow: start_task("ps", ["aux"])
  → OnRunProcess.run("ps", ["aux"]) → ProcessResult(stdout=...)
  → Projection via out_channel → Chat-Flow erhält Ergebnis
  → Chat-Flow: yield out_text(result.stdout)
```

Kein neuer Sicherheits-Code nötig — die Command Registry ist die Sicherheitsgrenze.
