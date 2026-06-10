from y5n.api.nodes import Node, NodeScope

from .runtime.os import run
from .runtime.setup import setup

os = Node(
    key="os",
    anonymous=True,
    setup=setup,
    run=run,
    navigable=True,
    resolvable=True,
    scope=NodeScope.GLOBAL,
)
