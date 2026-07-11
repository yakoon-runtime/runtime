from y5n.api.nodes import Node

from .runtime.os import run
from .runtime.setup import setup

os = Node(
    key="os",
    anonymous=True,  # GLOBAL
    setup=setup,
    run=run,
    navigable=False,
    resolvable=True,
)
