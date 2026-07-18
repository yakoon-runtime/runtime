from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import DOCUMENT


async def run(space: NodeSpace):
    identity = space.session.get_identity()

    projection = await space.ports.get(DOCUMENT)(
        space=space,
        state={"user": str(identity) if identity else None},
    )

    yield out(projection)
