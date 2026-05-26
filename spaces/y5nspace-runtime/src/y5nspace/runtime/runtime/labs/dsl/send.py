from y5n.api.flows import out, receive, send
from y5n.api.projections import to_text


async def run(_):

    yield send(
        "form.result",
        {
            "name": "runtime",
            "message": "Hello from send()",
        },
    )

    event = yield receive("form.result")
    text = to_text(f"Data: {event.data}")
    yield out(text)
