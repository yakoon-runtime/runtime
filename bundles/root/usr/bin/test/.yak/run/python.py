from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text


async def run(space: NodeSpace):

    greet = space.ports.get("greet")
    result = greet()
    yield out(to_text(result))
