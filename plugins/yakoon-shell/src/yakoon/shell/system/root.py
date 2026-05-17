from yakoon.base.nodes import Node
from yakoon.base.nodes.types import NodeScope

from .on_welcome import on_welcome

system = Node(
    key="system",
    name="System",
    anonymous=True,
    navigable=False,
)

system.add(
    Node(
        key="welcome",
        run=on_welcome,
        anonymous=True,
        scope=NodeScope.NODE,
    )
)
