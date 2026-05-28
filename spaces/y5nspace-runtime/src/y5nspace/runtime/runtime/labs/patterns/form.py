from y5n.api.flows import foreground, out, receive, suspend
from y5n.api.projections import to_text


async def run(_):

    yield foreground()

    while True:
        yield out(to_text("Vorname:"))
        event = yield receive()
        yield out(to_text(f"Result Vorname: {event.data}"))
        yield out(to_text("see 'jobs"))

        yield suspend()

        yield out(to_text("Nachname:"))
        event = yield receive()
        yield out(to_text(f"Result Nachname: {event.data}"))

        break
