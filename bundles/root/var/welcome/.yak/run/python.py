from y5n.api.dsl import out, view
from y5n.api.nodes import NodeSpace
from y5n.base.plugins.ports import OnProject


async def run(space: NodeSpace):
    projection = await space.ports.get(OnProject)(
        space=space,
        state={"name": space.request.payload},
    )
    yield view(clear=True)
    yield out(projection)
