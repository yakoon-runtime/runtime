from y5n.runtime.api.documents import to_text
from y5n.runtime.api.dsl import out, receive, send
from y5n.runtime.api.runtime import Event


async def run(_):
    yield send(
        channel="form.result",
        event=Event(
            payload={
                "name": "runtime",
                "message": "Hello from send()",
            }
        ),
    )

    event = yield receive("form.result")
    text = to_text(f"Payload: {event.payload}")
    yield out(text)
