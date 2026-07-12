from y5n.api.dsl import view
from y5n.api.nodes import NodeSpace


async def run(space: NodeSpace):
    yield view(clear=True)
