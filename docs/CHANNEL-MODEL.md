# Channel-Modell — Implementierter Scope-Resolver

## Kernidee

Ein Channel wird nicht durch seinen Speicherort adressiert, sondern durch einen **Scope-Resolver**.

```python
class Session:
    _channels: dict[str, deque[Event]]  # resolved key → queue
```

```python
def resolve(scope: Scope, channel: str, *, flow: Flow | None = None) -> str:
    if scope == Scope.FLOW:
        return f"{flow.id}:{channel}"          # flow-lokal
    elif scope == Scope.SESSION:
        return channel                           # session-global
    elif scope == Scope.USER_INPUT:
        return f"{flow.id}:__user__"             # user-input (channel ignoriert)
```

## Scopes

| Scope | Beispiel | Resolved Key | Owner | Lebenszyklus |
|---|---|---|---|---|
| `FLOW` | `receive("form.result")` | `{flow_id}:form.result` | Flow | Stirbt mit Flow |
| `SESSION` | `receive("cmd:abc", scope=SESSION)` | `cmd:abc` | Session | Stirbt mit Session |
| `USER_INPUT` | `receive("__user__", scope=USER_INPUT)` | `{flow_id}:__user__` | Flow | Stirbt mit Flow |

## Invarianten

```
FLOW Scope     → Owner = Flow     → Flow stirbt   → FLOW-Channels sterben
SESSION Scope  → Owner = Session  → Session stirbt → SESSION-Channels sterben
```

Implementiert in `Session.del_flow()` — alle Keys mit Prefix `{flow.id}:` werden aus `_channels` entfernt.

## API auf Session

```python
session.push_event(scope, channel, event, *, flow=None)
session.pop_event(scope, channel, *, flow=None) -> Event | None
session.has_mail(scope, channel, *, flow=None) -> bool
```

## API auf DSL-Ebene

```python
receive()                                            # FLOW, "default"
receive("form.result")                               # FLOW, "form.result"
receive("cmd:abc", scope=Scope.SESSION)               # SESSION, "cmd:abc"
receive("__user__", scope=Scope.USER_INPUT)           # USER_INPUT

send("form.result", event)                           # FLOW
send("cmd:abc", event, scope=Scope.SESSION)           # SESSION
send(..., scope=Scope.USER_INPUT)                     # → ValueError
```

## Validierung

- `USER_INPUT` erfordert `channel="__user__"` — sonst `ValueError`
- `send()` mit `USER_INPUT` → `ValueError` (USER_INPUT ist Receive-only)
- Validierung in `AwaitEvent.__init__()` (Effect-Ebene) und in `receive()`/`send()` (DSL-Ebene)

## Gebauter Stand (Spike, 2026-06-09)

- `Scope(Enum)` + `resolve()` in `y5n/base/flow/channel.py`
- `session._channels: dict[str, deque]` als einziger Speicherort
- `Flow.inbox`, `push_event`, `pop_event`, `has_mail` entfernt
- `Control.is_runnable(self, flow, session)` — alle Subklassen aktualisiert
- `AwaitEvent` + `EmitEvent` tragen `scope`-Parameter
- `receive()`/`send()` symmetrisch mit `scope`
- Engine: `EmitEvent` verwendet `effect.scope`, `_next_step` verwendet `flow.control.scope`
- Scheduler: `control.is_runnable(flow, session)`
- Runner: pusht aktuell noch auf `FLOW/"default"` (muss auf `USER_INPUT/"__user__"`)
- TaskRunner: pusht auf `FLOW/{task.channel}`
- `del_flow` räumt FLOW-Channels (`{flow_id}:*`)
- User-Input wird aktuell noch über `FLOW/"default"` geroutet

## Noch offen

1. **User-Input auf USER_INPUT umstellen**
   - Runner → `session.push_event(USER_INPUT, "__user__", event, flow=fg_flow)`
   - `receive()` → Default auf `USER_INPUT` statt `FLOW`?
   - Alle bestehenden `receive()`-Aufrufe in labs/examples prüfen

2. **Foreground-Routing**
   - USER_INPUT-Events nur an den aktuellen Vordergrund-Flow
   - Beim Foreground-Wechsel: alter Flow verliert __user__-Empfang

3. **`start_cmd` (CommandHandle + StartCommand-Effect)**
   - Nutzt SESSION-Scope für Channel `cmd:<uuid>`
   - Sub-Flow benachrichtigt Parent über SESSION-Channel

4. **SESSION-Channel-Lebenszyklus**
   - Aktuell: nie geräumt (außer bei Session-Tod)
   - Brauchen wir Cleanup für verwaiste SESSION-Channels?

---

Stand: 2026-06-09
