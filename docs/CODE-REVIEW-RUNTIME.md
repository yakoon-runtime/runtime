# Runtime Code Review — Juni 2026

Stand: `4a16d5ce` (alle High+Medium + 7 Low gefixt)

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
| ✅ M6 | `create_projection` + `compile_view` waren ungenutzt, Dateien gelöscht | `26978685` |
| ✅ M7 | `Outcome.__init__` hatte null Typannotationen | `26978685` |
| ✅ M8 | `TaskRunner._run()` behandelte `"sleep"` als magisches Built-in → entfernt. Nutze `delay()`! | `26978685` |
| ✅ M9 | `_ensure_step(run_fn)` war untypisiert | `26978685` |
| ✅ M10 | `FlowCursor.next()` fehlt Return-Type | `387aa53a` |
| ✅ M11 | `_handle_outcome(outcome)` untypisiert | `387aa53a` |
| ✅ M12 | `_call_runtime(callback)` untypisiert | `387aa53a` |

## LOW — bei Gelegenheit

| # | Problem | Datei:Zeile |
|---|---------|-------------|
| ✅ L1 | `Flow.view: Any | None` → `Projection | None` | `feefd65b` |
| ✅ L2 | `Effect` Base-Class ist leer (i.O., notiert) | `96ed4213` |
| L3 | `_schedule_waiting` ist O(n)-Scan → Reverse-Lookup einführen | `machine/scheduler.py:292` |
| ✅ L4 | Kommentierter Dead Code in engine.py (3 Blöcke) entfernt | `feefd65b` |
| ✅ L5 | Deutsche Comments → Englisch (engine, scheduler, parser, control) | `feefd65b` |
| ✅ L6 | `RuntimeHost.disconnect()` greift auf `runner._session` zu → `runner.session` Property | `4a16d5ce` |
| L7 | `SessionBuilder._counter` nicht thread-safe | `machine/session.py:16` |
| ✅ L8 | Hardcoded `None` für Context — `None` ist korrekt für system-setup | `(kein Fix nötig)` |
| ✅ L9 | `TaskRunner.start/_run` typisiert | `feefd65b` |
| ✅ L10 | `delay_until` in `__all__` von `y5n.base.flow` | `feefd65b` |
| L11 | `StartCommand`/`StartTask` validieren `channel` nicht | `primitives/effect.py:39,46` |
| L12 | Unreachable `raise` in `channel.py` (defensiv, okay) | `flow/channel.py:25` |

## Zusammenfassung

- **0 HIGH** — alle 7 erledigt (H1/H2/H4/H5/H6/H7 gefixt, H3 kein Bug)
- **12 MEDIUM** — alle gefixt
- **8 LOW** gefixt — 3 offen (L3/L7/L11/L12)

Die Core-Abstraktionen (Channel, Effect/Control, Scheduler) stehen gut.
Der Review findet vor allem Export-Lücken, ungenutzten Code und fehlende
Absicherung an den Rändern.
