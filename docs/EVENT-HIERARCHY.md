# Event in Yakoon

## Problem

`receive()` wartet heute auf mehrere Quellen, liefert aber immer `InputEvent`:

- User-Eingaben (`yield receive()`)
- Task-Results (`yield receive(task.channel)`)
- (bald) Timer, Mail, Webhooks, Agent-Responses

`InputEvent` für Task-Results zu verwenden ist ein semantischer Bruch:

```python
event = InputEvent(data=json.dumps(result), tokens=[], payload=result)
```

Der Empfänger muss wissen: "channel `task:abc` liefert Task-Result, also parst payload".

## Alternative 1: Event-Hierarchie (verworfen)

Eine flache Hierarchie mit `FlowEvent` als Basis und `InputEvent`, `TaskResultEvent`,
`TimerEvent` als Unterklassen. Ermöglicht `match/case` im Flow.

**Verworfen**, weil:

- Neue Quelle → neue Klasse (Klasseninflation)
- Runtime muss Event-Typen kennen
- Fighter dem Yakoon-Prinzip "bestehendes Konzept erweitern, kein neues einführen"

## Alternative 2: Event als Envelope (bevorzugt)

`InputEvent` wird zu `Event` — ein allgemeiner Envelope:

```python
@dataclass
class Event:
    payload: Any
    channel: str | None = None
```

Keine Hierarchie. Keine Unterklassen. `payload` trägt die Bedeutung.

### Quellen

```python
# User-Input
Event(payload="Stefan", channel="default")

# Task-Result
Event(payload={"returncode": 0, "stdout": "...", "file_name": "/tmp/foo.pdf"})

# Timer (später)
Event(payload={"expires_at": 1234.5})

# Agent (später)
Event(payload=AgentResponse(text="...", confidence=0.9))
```

### Flow

```python
event = yield receive(task.channel)

# payload ist polymorph – der Flow entscheidet, was er erwartet
match event.payload:
    case {"returncode": 0, "file_name": f}:
        yield out_text(f"PDF: {f}")
    case {"returncode": rc}:
        yield out_text(f"failed: {rc}")
    case str(s):
        yield out_text(f"user: {s}")
```

### TaskRunner

```python
# heute
flow.push_event(InputEvent(data=json.dumps(result), tokens=[], payload=result))

# morgen
flow.push_event(Event(payload={
    "returncode": 0,
    "stdout": "done",
    "file_name": "/tmp/foo.pdf",
}), channel=task.channel)
```

### Auswirkungen

| Aspekt | Änderung |
|--------|----------|
| `InputEvent` → `Event` | Neuer Name, `data: str` → `payload: Any` |
| `receive()` | Rückgabetyp dokumentiert als `Event`, sonst identisch |
| `TaskRunner` | `push_event(Event(payload=...))` statt `InputEvent(data=json.dumps(...))` |
| `Flow.inbox` | `defaultdict[str, deque[Event]]` statt `defaultdict[str, deque[InputEvent]]` |
| Engine | Keine Änderung – pusht Events in Inboxen, unabhängig vom Typ |
| Bestehende Flows | `event.data` → `event.payload` (oder `event.data` bleibt als Kompat-Alias) |

### Gewonnene Erkenntnis

> *Immer wenn Yakoon neue Fähigkeiten bekam, wurde die Runtime nicht komplexer.
> Sondern allgemeiner.*

`InputEvent` bedeutete früher "Benutzer hat etwas getippt". Heute bedeutet es
"Irgendetwas ist passiert". Der Name `InputEvent` wird dieser Bedeutung nicht mehr
gerecht – `Event` schon.

Der Inhalt wandert vollständig in `payload: Any`. Channel, Inbox und `receive()`
bleiben unverändert. Die Runtime wird nicht komplexer, sondern allgemeiner.

## Nächste Schritte

1. `InputEvent` → `Event` umbenennen, `data` → `payload` (mit Kompat-Alias)
2. `TaskRunner._run()` auf `Event(payload=...)` umstellen
3. PDF-Demo auf `event.payload["file_name"]` umstellen
4. `Form` prüfen: liefert Form auch `Event(payload=value)` statt `InputEvent`?
