from y5n.api.dsl import foreground, out, prompt, receive
from y5n.api.projections import to_text


async def run(_):
    yield foreground()

    yield prompt(to_text("Vorname:"))
    event_fn = yield receive()

    yield prompt(to_text("Nachname:"))
    event_ln = yield receive()

    yield out(to_text("\nEingabe:"))
    yield out(to_text(f"{event_fn.payload}, {event_ln.payload}"))
