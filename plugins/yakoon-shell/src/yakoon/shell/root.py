from yakoon.base.nodes import (
    Node,
    RuntimeContext,
)

from .resource import get_resource
from .system import system


async def boot_shell(ctx: RuntimeContext):
    pass


# ----------------------------------
# SHELL NODE
# ----------------------------------

shell = Node(
    key="shell",
    name="Shell",
    is_shell=True,
    anonymous=True,
    on_setup=boot_shell,
    on_resource=get_resource,
)

shell.mount(system)
