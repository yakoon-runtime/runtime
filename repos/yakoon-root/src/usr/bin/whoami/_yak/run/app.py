from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT


async def run(space: NodeSpace):
    identity = space.session.get_identity()

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"user": str(identity) if identity else None},
    )

    yield out(projection)
