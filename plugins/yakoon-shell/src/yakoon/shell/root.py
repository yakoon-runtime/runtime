from yakoon.base.nodes import Node

from .resources import on_resource
from .system import system

# ----------------------------------
# SHELL
# ----------------------------------

shell = Node(
    key="shell",
    name="Shell",
    is_shell=True,
    anonymous=True,
    on_resource=on_resource,
)

shell.mount(system)
