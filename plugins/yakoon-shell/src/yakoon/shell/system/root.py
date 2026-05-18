from yakoon.base.nodes import Node
from yakoon.base.nodes.types import NodeScope

from .on_cd import on_cd
from .on_list import on_list
from .on_version import on_version
from .on_welcome import on_welcome

system = Node(
    key="system",
    name="System",
    anonymous=True,
    navigable=True,
    resolvable=False,
)

system.add(
    Node(
        key="welcome",
        on_run=on_welcome,
        anonymous=True,
        scope=NodeScope.NODE,
        resolvable=True,
        navigable=True,
    )
)

system.add(
    Node(
        key="version",
        on_run=on_version,
        anonymous=True,
        scope=NodeScope.NODE,
        resolvable=True,
        navigable=False,
    )
)

system.add(
    Node(
        key="ls",
        on_run=on_list,
        anonymous=True,
        scope=NodeScope.GLOBAL,
        resolvable=True,
        navigable=False,
    )
)

system.add(
    Node(
        key="cd",
        on_run=on_cd,
        anonymous=True,
        scope=NodeScope.GLOBAL,
        resolvable=True,
        navigable=False,
    )
)
