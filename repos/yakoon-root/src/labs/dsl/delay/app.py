from y5n.api.documents import to_text
from y5n.api.dsl import delay, out


async def run(_):
    text = to_text("Wait for 5 seconds\n...")
    yield out(text)

    yield delay(5)

    text = to_text("Done!")
    yield out(text)
