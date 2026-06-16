# LLM-Architektur — Diskussionsstand

## Prämisse

**LLM ist kein Spezialfall.** Genauso wie `InputEvent → Event(payload)` und
`OS-Prozess → Task` verallgemeinert wurden, wird LLM nicht als Magie in die
Runtime eingebaut.

LLM ist Fachlichkeit — keine Runtime-Primitive.

---

## Architektur

```
y5ncore-base                          # Vertrag (null deps)
  └── y5n.base.llm
        ├── LLMRequest
        ├── LLMResponse
        └── OnCallLLM (Protocol)

y5ncore-llm                           # Gemeinsame Provider (httpx etc.)
  └── y5n.llm.providers
        ├── ollama.py
        ├── openai_compat.py
        └── gemini.py

Node Setup
  → from y5n.llm.providers.ollama import OllamaProvider
  → ctx.ports.set(OnCallLLM, OllamaProvider(...))

Flow
  → ctx.ports.get(OnCallLLM)
  → llm.complete(LLMRequest(prompt=...))
  → LLMResponse
```

### Port first, Task second

Der Port kommt **vor** der Ausführungsstrategie.

```python
class OnCallLLM(Protocol):
    async def complete(self, request: LLMRequest) -> LLMResponse: ...
```

Fachlich existiert zuerst: *"Ich möchte ein LLM benutzen."*
Erst danach: *"Wie wird das ausgeführt?"* — als Task.

### Provider ist Node-lokal

Die Port-Registry ist **nicht global**. Jeder Node setzt seinen eigenen
Provider via `setup()`:

```python
from y5n.llm.providers.ollama import OllamaProvider
from y5n.base.ports import OnCallLLM

# Runtime-Space
ctx.ports.set(OnCallLLM, OllamaProvider(...))

# Accounting-Space
ctx.ports.set(OnCallLLM, OpenAIProvider(...))

# Research-Space
ctx.ports.set(OnCallLLM, ClaudeProvider(...))
```

Kein globales Registry-System, kein AIManager, keine ProviderFactory.
Yakoon kann je nach Space, Node oder Domain eine andere KI verwenden.

Die gemeinsamen Provider liegen in `y5n.llm.providers` im Package
`y5ncore-llm` (jeder Space kann sie importieren), aber ein Space
kann auch einen eigenen Provider bauen — das Port-Protokoll
(`OnCallLLM`) ist in `y5n.base.llm` und bindet an keine Implementierung.

### TaskRunner weiß nichts von LLM

`run_task("llm")` wird es nicht geben. Der TaskRunner bekommt ein Callable:

```python
llm = ctx.ports.get(OnCallLLM)
task = run_task(llm.complete, request)
yield task
response = yield receive(task.channel)
```

Der TaskRunner führt aus. Er muss nicht wissen, ob dahinter OpenAI,
Ollama oder ein lokales Modell steckt.

---

## Zwei Phasen

### Phase 1 — Explizit

Der erste Spike zeigt jeden Schritt sichtbar:

```python
llm = ctx.ports.get(OnCallLLM)

task = run_task(
    llm.complete,
    request,
)

yield task

response = yield receive(task.channel)
```

**Disziplin:** Kein Verstecken hinter Convenience. Der Flow sieht:

```text
Port → Task → Channel
```

Diese Phase lehrt uns, was wirklich gebraucht wird.

### Phase 2 — Convenience (wenn das Muster stabil ist)

Erst wenn Phase 1 langweilig geworden ist:

```python
response = yield ask("Schreibe eine Rechnung ...")
```

`ask()` ist kein Runtime-Primitive, sondern LLM-DSL — Convenience über
dem expliziten Pfad. Genau wie `out_text()` Convenience über `out()` ist.

```python
def ask(prompt: str) -> ...:
    llm = ctx.ports.get(OnCallLLM)
    request = LLMRequest(prompt=prompt)
    task = run_task(llm.complete, request)
    yield task
    return receive(task.channel)
```

---

## Datenfluss

```
Flow
  → ctx.ports.get(OnCallLLM)     Port auflösen
  → run_task(llm.complete, ...)  Task starten
    → llm.complete                Port-Implementierung
      → Provider                  Ollama / OpenAI / Claude
        → HTTP / SDK
    ← LLMResponse
  ← channel
  → yield receive(channel)
```

---

## Anti-Pattern: Agent-Framework

Was wir **nicht** tun:

```text
LLM → Agent → Multi-Agent → Supervisor → Planner → Framework → 20000 LOC
```

Ein Agent ist nichts anderes als:

```python
async def agent():
    answer = await llm(...)
```

Der Rest ist Orchestrierung — und Orchestrierung kann Yakoon bereits
mit Flow, Task, Event.

---

## Channel-Vertrag

Der Channel ist der API-Vertrag zwischen Task und Flow.

**Single Response:**

```python
Event(payload=LLMResponse(text="...", model="llama3", usage={...}))
```

**Streaming (später):**

```python
Event(payload=TokenChunk(text="Hallo", index=0, final=False))
Event(payload=TokenChunk(text=" Welt", index=1, final=False))
Event(payload=TokenChunk(text="", index=2, final=True, usage={...}))
```

Der Channel (`defaultdict[str, deque[Event]]`) trägt mehrere Events.
Für Batch reicht `yield receive(channel)`, für Streaming braucht es
`receive_all()` oder eine Channel-Iteration.

---

## Models in `y5n.base`

`LLMRequest`/`LLMResponse` gehören nach `y5n.base` — weil sie von Spaces,
Providern und Tasks importiert werden. Kein Provider soll `y5n.runtime`
importieren müssen. Analog zu `RuntimeInfo`.

---

## Roadmap

### Schritt 1 — Phase-1-Spike

- `OnCallLLM`-Port + `LLMRequest`/`LLMResponse` in `y5n.base` (`y5ncore-base`)
- Gemeinsame Provider in `y5n.llm.providers` (`y5ncore-llm`) — Ollama, OpenAI-Compat, Gemini
- Jeder Space importiert Provider aus `y5n.llm.providers` und registriert per `ctx.ports.set(OnCallLLM, ...)`
- Flow: `ctx.ports.get()` → `llm.complete()` → `out_text()`
- Momentan noch direktes `await` (kein Task-Wrapper) — Task-Wrapper folgt in Phase 2

### Schritt 2 — Provider-Auswahl pro Space

- Zweiter Provider (OpenAI / Claude)
- Space entscheidet via `setup()`
- Mehrere Spaces mit unterschiedlichen Providern parallel

### Schritt 3 — Phase 2: `ask()`-Convenience

- Erst wenn das Muster stabil und langweilig ist
- `ask()` als reiner Wrapper über dem expliziten Pfad

### Schritt 4 — Tools / Function Calling

- `LLMRequest` um `tools` erweitern
- Provider kann `ToolCall` zurückgeben
- Flow führt Tool aus, Ergebnis zurück ins Modell

### Schritt 5 — Structured Output

- `response_format` in `LLMRequest`
- Antwort als JSON/Objekt statt freiem Text

### Schritt 6 — Agent (viel später)

- Flow orchestriert: prompt → tool → prompt → tool → done
- Kein neuer Agent-Begriff nötig — ein Flow ist der Agent

---

## Offene Fragen

1. Streaming: Schritt 1 oder später?
2. `ToolCall`-Modell: Wie sieht das minimale Interface aus?
3. History/Memory: Im Port oder im Flow?
4. `run_task(callable, ...)` — welche Signatur? `run_task(fn, *args, **kwargs)`?
