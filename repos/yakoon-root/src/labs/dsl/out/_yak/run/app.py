from y5n.api.dsl import out
from y5n.api.projections import to_text


async def run(_):
    text = to_text("Hello out!")
    yield out(text)
