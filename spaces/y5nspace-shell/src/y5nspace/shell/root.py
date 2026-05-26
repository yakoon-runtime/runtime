from y5n.api.nodes import Node

from .on_setup import on_setup
from .system import system

# ----------------------------------
# SHELL
# ----------------------------------

shell = Node(
    key="shell",
    name="Shell",
    is_shell=True,
    anonymous=True,
    setup=on_setup,
)

shell.mount(system)
