from y5n.api.flows import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    # raise DomainError("Test")

    path = space.session.get_current_node()  # type: ignore
    yield out(to_text("\n" + str(path)))
