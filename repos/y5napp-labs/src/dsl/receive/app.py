from y5n.runtime.api.documents import to_text
from y5n.runtime.api.dsl import delay, out, receive


async def run(_):
    yield out(to_text("receive suspended in background... see 'jobs'"))
    while True:
        event = yield receive()
        if not event:
            yield delay(5)
        else:
            yield out(to_text(f"Result: {event.payload}"))
