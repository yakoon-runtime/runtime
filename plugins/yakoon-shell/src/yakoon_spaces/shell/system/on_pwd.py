from yakoon.api.flows import out
from yakoon.api.nodes import NodeSpace
from yakoon.api.projections import to_text
from yakoon.base.runtime.errors import DomainError

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_pwd(space: NodeSpace):

    raise DomainError("Test")

    path = space.session.get_current_node()
    yield out(to_text("\n" + str(path)))
