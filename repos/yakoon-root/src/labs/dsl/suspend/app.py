from y5n.api.documents import to_text
from y5n.api.dsl import foreground, out, receive, suspend


async def run(_):
    yield foreground()

    yield out(to_text("Vorname:"))
    event = yield receive()
    yield out(to_text(f"Result Vorname: {event.payload}"))

    yield out(to_text("see 'jobs"))
    yield suspend()

    yield out(to_text("Nachname:"))
    event = yield receive()
    yield out(to_text(f"Result Nachname: {event.payload}"))
