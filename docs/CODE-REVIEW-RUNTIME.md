# Runtime Code Review — Juni 2026

Stand: `e8357ac4` (start_cmd + start_task)

## HIGH — vor nächstem Feature fixen

### H1 — `start_cmd` fehlt in `__all__`

**Datei:** `runtime/y5ncore-base/src/y5n/base/flow/__init__.py:16-28`

`start_cmd` wird aus `dsl.py` importiert (Zeile 10) aber nicht in `__all__` gelistet.
`from y5n.base.flow import *` droppt es. `y5n.api.dsl.__init__` exportiert es korrekt.

**Fix:** `"start_cmd"` in `__all__` aufnehmen.

---

### H2 — `getattr` in `FlowCursor.next()`

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/flow/cursor.py:29`

```python
handler = getattr(node, self.handler_name)
```

Gibt jeden beliebigen Attributnamen weiter (`__class__`, `__init__`, ...).
`handler_name` ist als `Literal["run", "setup"]` typisiert, aber nicht runtime-geprüft.

**Fix:** Explizites Dispatch via `if/elif`:

```python
if self.handler_name == "run":
    handler = node.run
elif self.handler_name == "setup":
    handler = node.setup
else:
    raise ValueError(f"Ungültiger Handler: {self.handler_name}")
```

---

### H3 — `Suspend` hängt für immer

**Datei:** `runtime/y5ncore-base/src/y5n/base/flow/primitives/control.py:46-54`

`Suspend` definiert `resume()` (setzt `flow.control = YieldToScheduler()`), aber `resume()`
wird **nirgends aufgerufen**. Jeder Flow, der `yield suspend()` macht, blockiert permanent.

**Fix:** Resume-Mechanismus implementieren (z.B. Command, der auf `Suspend`-geblockte Flows lostritt)
oder `suspend()` als Feature entfernen, bis es gebraucht wird.

---

### H4 — Layer-Verletzung: `y5ncore-base` importiert aus `runtime`

**Dateien:**
- `runtime/y5ncore-base/src/y5n/base/flow/channel.py:7`
- `runtime/y5ncore-base/src/y5n/base/flow/primitives/control.py:10`

Beide importieren `from y5n.runtime.flow import Flow` (TYPE_CHECKING-geguard).

Es existiert bereits ein `Flow`-Protocol in `y5n.base.flow.protocol.py`, das nie verwendet wird.

**Fix:** Für TYPE_CHECKING-Kontexte das Protocol aus `y5n.base.flow.protocol` nutzen
statt des konkreten `Flow` aus dem Runtime-Package.

---

### H5 — `session._runtime_flow_id` mit `# type: ignore`

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/machine/engine.py:129,189`

```python
session._runtime_flow_id = flow.id  # type: ignore
```

Engine greift in privates Attribut von Session und ignoriert den Typechecker.
Entweder öffentliche Methode auf Session oder Flow-ID explizit durchreichen.

**Fix:** `session` um `set_runtime_flow_id(flow_id)` ergänzen oder die ID über
den Call-Stack parametrisieren.

---

### H6 — Inkonsistente Benennung `channel` vs `result_channel`

| Ort | Name |
|-----|------|
| `StartTask.__init__` | `channel` |
| `StartCommand.__init__` | `channel` |
| `OnTaskStart` Protocol | `channel` |
| `OnCommandStart` Protocol | `result_channel` |
| `engine.py` `_apply_effects` (start_task) | `channel=effect.channel` |
| `engine.py` `_apply_effects` (start_cmd) | `result_channel=effect.channel` |
| `task.py` `TaskRunner.start` | `channel` |
| `wire/machine.py` `on_start_command` | `result_channel` |
| `dsl.py` `start_task()` | `result_channel` |
| `dsl.py` `start_cmd()` | `result_channel` |

Auf der DSL-Ebene ist es `result_channel` (gut). In den darunterliegenden Schichten
wechselt es zwischen `channel` und `result_channel`.

**Fix:** Standardisieren auf `result_channel` auf allen Ebenen.

---

### H7 — `InputParser.parse()` validiert Payload nicht

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/machine/parser.py:10-27`

`parse()` erhält `event.payload` ohne Typ- oder Leer-Check. Bei `None`, Integer
oder Leerstring crasht `shlex.split()` downstream.

**Fix:**
```python
if not isinstance(event.payload, str) or not event.payload.strip():
    return "", [], []
```

---

## MEDIUM — nächste Gelegenheit

| # | Problem | Datei:Zeile |
|---|---------|-------------|
| M1 | `Flow.has_stack()` greift auf `cursor._stack` zu statt `cursor.has_stack()` zu delegieren | `flow/flow.py:35` |
| M2 | `RuntimeHost._runner_key()` ist tot (definiert, nie aufgerufen) | `machine/host.py:92` |
| M3 | `OnBootstrapPermissions` in `wire/machine.py` nirgends referenziert | `wire/machine.py:206` |
| M4 | `OnContinuePipeline` in `engine.py` tot | `machine/engine.py:354` |
| M5 | `OnApplyPermissions` in `session.py` tot | `machine/session.py:44` |
| M6 | `create_projection` + `compile_view` exportiert aber nie konsumiert | `primitives/{builder,view}.py` |
| M7 | `Outcome.__init__` hat null Typannotationen | `primitives/outcome.py:5-6` |
| M8 | `TaskRunner._run()` behandelt `"sleep"` als magisches Built-in | `machine/task.py:24` |
| M9 | `_ensure_step(run_fn)` untypisiert | `flow/cursor.py:57` |
| M10 | `FlowCursor.next()` fehlt Return-Type | `flow/cursor.py:23` |
| M11 | `_handle_outcome(outcome)` untypisiert | `machine/scheduler.py:264` |
| M12 | `_call_runtime(callback)` untypisiert | `machine/scheduler.py:237` |

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

- **7 HIGH** — davon 4 schnell fixbar (H1/H2/H6/H7), 3 brauchen Design-Entscheidung (H3/H4/H5)
- **12 MEDIUM** — hauptsächlich Dead Code und fehlende Typannotationen
- **13 LOW** — Hygiene, kleine Präzisionsprobleme

Die Core-Abstraktionen (Channel, Effect/Control, Scheduler) stehen gut.
Der Review findet vor allem Export-Lücken, ungenutzten Code und fehlende
Absicherung an den Rändern.
