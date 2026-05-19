from yakoon.base.nodes import Node

from .resources import get_resource
from .system import system

# ----------------------------------
# SHELL NODE
# ----------------------------------

shell = Node(
    key="shell",
    name="Shell",
    is_shell=True,
    anonymous=True,
    on_resource=get_resource,
)

shell.mount(system)
