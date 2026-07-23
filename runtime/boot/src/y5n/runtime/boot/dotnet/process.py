from y5n.runtime.api.flow.dsl import out_text


async def run(space):
    yield out_text(".NET host is not yet supported — coming in a future release.")
