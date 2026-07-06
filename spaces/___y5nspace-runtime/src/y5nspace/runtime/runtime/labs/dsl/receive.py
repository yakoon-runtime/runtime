from y5n.api.dsl import delay, out, receive
from y5n.api.projections import to_text


async def run(_):

    yield out(to_text("receive suspended in background... see 'jobs'"))
    while True:
        event = yield receive()
        if not event:
            yield delay(5)
        else:
            yield out(to_text(f"Result: {event.payload}"))
