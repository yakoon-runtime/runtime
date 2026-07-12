from y5n.api.dsl import out, view
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT

from .modules.identity import IDENTITY
from .modules.shell import SHELL_NAME
from .ports import GREET


async def run(space: NodeSpace):
    greet = space.ports.get(GREET)
    result = greet("John", "Doe")

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"greeting": result, "identity": IDENTITY, "shell": SHELL_NAME},
    )

    yield view(clear=True)
    yield out(projection)
