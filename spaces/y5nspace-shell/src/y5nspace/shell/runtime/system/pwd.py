from y5n.api.flows import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text
from y5n.base.runtime.errors import DomainError

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    raise DomainError("Test")

    path = space.session.get_current_node()
    yield out(to_text("\n" + str(path)))
