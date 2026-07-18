from y5n.api.documents import to_text
from y5n.api.dsl import out


async def run(_):
    text = to_text("Hello out!")
    yield out(text)
