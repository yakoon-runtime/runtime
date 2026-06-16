# ADA: Flow → Task (minimal)

> **Status:** Entwurf
> **Datum:** 2026-06-06

---

## 1. Problem

Heute kann ein Flow **keine Arbeit delegieren** und auf das Ergebnis warten.

`yield form.ask(...)` suspendiert den Flow und wartet auf User-Input – das ist
ein interaktives Primitive. Es gibt aber kein Primitive für:

> "Starte Berechnung X, mach weiter, sobald das Ergebnis da ist."

Beispiele:
- PDF generieren (CPU-intensiv, keine UI)
- API aufrufen (I/O-bound, keine UI)
- Datenbank-Job (langlaufend, keine UI)

---

## 2. Entscheidung

Wir führen **ein** neues Primitive ein:

```python
task_id = yield run_task(command, **kwargs)
```

und nutzen das bestehende:

```python
result = yield receive(f"task:{task_id}")
```

### 2.1 `run_task`

- Startet einen **Task** (kein Flow)
- Liefert sofort `task_id` zurück → der Flow läuft weiter
- Der Task hat: `run(**kwargs) → return result`
- Kein UI, keine Projection, keine Jobs, kein `yield`
- Reine Berechnung

### 2.2 Kommunikation über Events

Der Task sendet sein Ergebnis per Event zurück:

```python
# Task-intern
emit(Event(f"task:{task_id}", result))
```

Der Flow empfängt es mit:

```python
result = yield receive(f"task:{task_id}")
```

### 2.3 Bestehende Konzepte

| Primitive | Existiert | Zweck |
|---|---|---|
| `receive(channel)` | ja | Wartet auf Event im Channel |
| `send(channel, event)` | ja | Sendet Event in Channel |
| `EmitEvent` | ja | Task kommuniziert Ergebnis |
| `AwaitEvent` | ja | Flow wartet auf Ergebnis |

`run_task` ist das einzige neue Primitive – und es ist nur eine
Dispatcher-Fassade.

---

## 3. Flow vs Task

### Flow
- Hat `yield` → interaktiv
- Hat Projection → UI
- Hat `receive` / `suspend` → Lebenszyklus
- Läuft als **Job** im Scheduler

### Task
- Nur `run(**kwargs) → return result`
- Kein `yield`, keine Projection, keine Jobs
- Reine Berechnung,同步 oder async
- Läuft außerhalb des Schedulers (Threadpool oder direkter Aufruf)

### Beispiel

```python
async def run(_):
    task_id = yield run_task("generate_pdf", customer_id=123)
    pdf = yield receive(f"task:{task_id}")
    yield out_text(f"PDF erzeugt: {pdf}")
```

Der Flow:
1. Startet `generate_pdf` als Task → bekommt `task_id`
2. Macht `receive("task:...")` → suspendiert, wartet auf Event
3. Task läuft, sendet Ergebnis via `emit(Event("task:...", pdf))`
4. Flow wird resumed, Ergebnis ist da

---

## 4. Flow startet Flow (später)

Erst wenn ein Flow **einen anderen Flow** starten und dessen Projection sehen
will, brauchen wir Spawn/Join. Das ist ein separater Schritt und explizit
nicht Teil dieser ADA.

Beispiel für *später*:

```python
sub_job_id = yield spawn_flow("create_invoice", customer=...)
yield join(sub_job_id)  # Parent wartet, Kind projiziert
```

Aktuell würde ich nicht einmal sagen, ob `spawn_flow` nötig ist – denn der
Cursor-Stack (`cursor.push()`) erlaubt bereits `yield subflow()` als
sequentiellen Aufruf ohne neuen Job:

```python
async def run(_):
    yield create_invoice()  # sub-generator, gleicher Job
```

Das ist call/return, nicht spawn/join – aber vielleicht reicht das.

---

## 5. Was wir nicht bauen (Phase 1)

| Konzept | Grund |
|---|---|
| ProcessRegistry | `run_task` ruft eine registrierte Funktion auf (einfacher Dispatch) |
| Spawn/Join | Flow-startet-Flow ist erstmal nicht nötig |
| Job-Tree | Runtime sieht nur `{job_17, job_18}`. UI kann später Bäume bauen |
| Task-Projection | Task hat keine UI. Ergebnisse werden per Event kommuniziert |

---

## 6. Offene Fragen

- Soll `run_task` einen Threadpool nutzen oder `asyncio.create_task`?
- Wie wird ein Task registriert? (separates Registry oder `@task`-Dekorator?)
- Fehlerfall: Task wirft Exception → Event mit Fehler oder raise im Flow?
