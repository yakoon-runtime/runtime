from y5n.api.nodes import Node

from .runtime.setup import setup
from .runtime.system.space import system

# ----------------------------------
# SHELL
# ----------------------------------

shell = Node(
    key="shell",
    name="Shell",
    is_shell=True,
    anonymous=True,
    setup=setup,
)

shell.mount(system)
