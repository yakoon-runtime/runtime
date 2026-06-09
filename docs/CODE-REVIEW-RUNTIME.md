# Runtime Code Review — Juni 2026

Stand: `6e093c6b` (alle High gefixt)

## HIGH — vor nächstem Feature fixen

### ✅ H1 — `start_cmd` fehlt in `__all__`

**Gefixt in:** `85eaa7e`

---

### ✅ H2 — `getattr` in `FlowCursor.next()`

**Gefixt in:** `a847caac`

---

### ✅ H3 — `Suspend` hängt für immer

**Kein Bug.** `Suspend` ist ein Protokoll für das Job-System (analog zu Ctrl+Z / `bg` / `fg`).
Der Flow blockiert, bis der Job-Manager über `jobs.py` `resume()` aufruft.

`resume()` wird in `y5nspace` von der Job-Verwaltung getriggert — nicht von der Runtime.
Der Eintrag bleibt als Hinweis, kein Fix nötig.

---

### ✅ H4 — Layer-Verletzung: `y5ncore-base` importierte `Flow` aus `runtime`

**Gefixt in:** `fc484d42`

---

### ✅ H5 — `session._runtime_flow_id` mit `# type: ignore`

**Gefixt in:** `7cab5444` (entfernt — war toter Code)

---

### ✅ H6 — Inkonsistente Benennung `channel` vs `result_channel`

**Gefixt in:** `84fa0b7f` (auf `channel` vereinheitlicht)

---

### ✅ H7 — `InputParser.parse()` validiert Payload nicht

**Gefixt in:** `95ea4800`

---

## MEDIUM — nächste Gelegenheit

| # | Problem | Datei:Zeile |
|---|---------|-------------|
| ✅ M1 | `Flow.has_stack()` greift auf `cursor._stack` zu statt `cursor.has_stack()` zu delegieren | `a847caac` |
| ✅ M2 | `RuntimeHost._runner_key()` war tot (definiert, nie aufgerufen) | `6e093c6b` |
| ✅ M3 | `OnBootstrapPermissions` in `wire/machine.py` war tot | `387aa53a` |
| ✅ M4 | `OnContinuePipeline` in `engine.py` war tot | `6e093c6b` |
| ✅ M5 | `OnApplyPermissions` in `session.py` war tot | `6e093c6b` |
| M6 | `create_projection` + `compile_view` exportiert aber nie konsumiert | `primitives/{builder,view}.py` |
| ✅ M7 | `Outcome.__init__` hatte null Typannotationen | `(wartet auf Commit)` |
| M8 | `TaskRunner._run()` behandelt `"sleep"` als magisches Built-in | `machine/task.py:24` |
| ✅ M9 | `_ensure_step(run_fn)` war untypisiert | `(wartet auf Commit)` |
| ✅ M10 | `FlowCursor.next()` fehlt Return-Type | `387aa53a` |
| ✅ M11 | `_handle_outcome(outcome)` untypisiert | `387aa53a` |
| ✅ M12 | `_call_runtime(callback)` untypisiert | `387aa53a` |

## LOW — bei Gelegenheit

| # | Problem | Datei:Zeile |
|---|---------|-------------|
| L1 | `Flow.view: Any | None` → `Projection | None` | `flow/flow.py:25` |
| L2 | `Effect` Base-Class ist leer (i.O., notiert) | `primitives/effect.py:9` |
| L3 | `_schedule_waiting` ist O(n)-Scan → Reverse-Lookup einführen | `machine/scheduler.py:292` |
| L4 | Kommentierter Dead Code in engine.py (3 Blöcke) | `machine/engine.py:72-108` |
| L5 | Deutsche + Englische Comments gemischt | mehrere Dateien |
| L6 | `RuntimeHost.disconnect()` greift auf `runner._session` zu | `machine/host.py:77` |
| L7 | `SessionBuilder._counter` nicht thread-safe | `machine/session.py:16` |
| L8 | Hardcoded `None` für Context in Engine | `machine/engine.py:282` |
| L9 | `TaskRunner.start/_run` komplett untypisiert | `machine/task.py:19-22` |
| L10 | `delay_until` fehlt in `__all__` von `y5n.base.flow` | `flow/__init__.py` |
| L11 | `StartCommand`/`StartTask` validieren `channel` nicht | `primitives/effect.py:39,46` |
| L12 | Unreachable `raise` in `channel.py` (defensiv, okay) | `flow/channel.py:25` |

## Zusammenfassung

- **0 HIGH** — alle 7 erledigt (H1/H2/H4/H5/H6/H7 gefixt, H3 kein Bug)
- **12 MEDIUM** — hauptsächlich Dead Code und fehlende Typannotationen
- **13 LOW** — Hygiene, kleine Präzisionsprobleme

Die Core-Abstraktionen (Channel, Effect/Control, Scheduler) stehen gut.
Der Review findet vor allem Export-Lücken, ungenutzten Code und fehlende
Absicherung an den Rändern.
