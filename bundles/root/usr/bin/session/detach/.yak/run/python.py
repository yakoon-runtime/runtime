from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import SESSION_DETACH
from y5n.api.projections import to_text


async def run(space: NodeSpace):
    yield out(to_text("Detached"))

    on_detach = space.ports.get(SESSION_DETACH)
    await on_detach(session=space.session)
