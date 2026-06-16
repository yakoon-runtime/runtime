# Job Tree / Subprocess Exploration

> **Datum:** 2026-06-06
> **Status:** Entwurf — zwei parallele Ansätze, nicht abgeschlossen

Zwei Vorschläge, wie ein Flow Arbeit delegieren kann. Geschrieben am selben Tag als alternative Ansätze.

---

## Proposal A: Minimal — Flow → Task

Kernidee: Ein neues Primitive `run_task` für delegierte Arbeit ohne UI.

```python
task_id = yield run_task("generate_pdf", customer_id=123)
result = yield receive(f"task:{task_id}")
```

### Flow vs Task

| | Flow | Task |
|---|---|---|
| `yield` | ja (interaktiv) | nein |
| Projection | ja | nein |
| Scheduler | Job | Threadpool / direkt |
| Lebenszyklus | suspend/resume | `run() → result` |

### Was nicht gebaut wird (Phase 1)

- ProcessRegistry — `run_task` ruft registrierte Funktion auf
- Spawn/Join — Flow startet Flow erstmal nicht nötig
- Job-Tree — UI kann später Bäume bauen
- Task-Projection — Task hat keine UI

**Offene Fragen:**
- Threadpool vs `asyncio.create_task`?
- `@task`-Dekorator vs separate Registry?
- Fehlerfall: Event mit Exception oder raise im Flow?

---

## Proposal B: Spawn/Join — Job Tree

Kernidee: `Process` als first-class Node, Spawn/Join im Protocol, Job-Tree in der Projection.

```python
def create_invoice(session, customer: str):
    items = yield form.ask("select items ...")
    pdf = yield spawn("generate_pdf", items=items, mode="foreground")
    yield spawn("send_mail", attachment=pdf, mode="background")
    yield show("Invoice created")
```

### Neue Konzepte

1. **Process** — Generator (wie Command), registriert in ProcessRegistry
2. **SpawnProcess / JoinProcess** — InputEvent-Varianten
3. **Process-Node in Projection** — Baumstruktur im Patch-Protokoll

### Agent

> Agent = Job, der andere Jobs starten darf.

Keine LLM-Entscheidung, sondern Runtime-Entscheidung. Ein Agent ist ein Process, der `spawn()` verwendet.

### Fahrplan

1. ProcessRegistry
2. SpawnProcess / JoinProcess im Protocol
3. Spawn/Join-Handling im Runner
4. Process-Node in Projection
5. Client-Rendering (verschachtelte Gruppen)
6. Background-Mode
7. Persistence

**Offene Fragen:**
- `yield spawn()` (blockierend) vs await-ähnlich?
- Wie tief darf der Job-Tree?
- Cascade-Cancel bei Parent-Failure?
- `cancel(job_id)`-Befehl?

---

## Vergleich

| Aspekt | Proposal A (Task) | Proposal B (Spawn/Join) |
|---|---|---|
| Neu | `run_task` | Spawn, Join, ProcessRegistry, Process-Node |
| Komplexität | Minimal | Mittel |
| Parallelität | Serial (receive wartet) | foreground/background |
| UI-Auswirkung | Keine | Job-Tree in Projection |
| Nutzen | PDF, API, DB-Jobs | `deploy`-Pipeline, Agents |
| Blockiert durch | Nichts | Projection-Baum, Client-Rendering |

Beide Ansätze schließen sich nicht aus. A ist sofort realisierbar, B braucht mehr Infrastruktur.
