from y5n.api.nodes import Node

from .runtime.ident.space import ident
from .runtime.setup import setup

# ----------------------------------
# SHELL
# ----------------------------------

shell = Node(
    key="shell",
    name="Shell",
    anonymous=True,
    resolvable=False,
    navigable=True,
    setup=setup,
)


# ----------------------------------
# MOUNT
# ----------------------------------

shell.mount(ident)
