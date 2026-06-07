from y5n.api.invocations import Invocation
from y5n.api.nodes import Node, NodeScope

from .cd import run as cd
from .clear import run as clear
from .ls import run as ls
from .man import run as man
from .pwd import run as pwd

# ----------------------------------
# SYSTEM
# ----------------------------------

system = Node(
    key="system",
    name="System",
    anonymous=True,
    navigable=True,
    resolvable=False,
)


# ----------------------------------
# MAN
# ----------------------------------

system.add(
    Node(
        key="man",
        run=man,
        anonymous=True,
        scope=NodeScope.GLOBAL,
        resolvable=True,
        navigable=False,
        invocations=[
            Invocation(args=["command"], default=True),
        ],
    )
)

# ----------------------------------
# LS - LIST
# ----------------------------------

system.add(
    Node(
        key="ls",
        run=ls,
        anonymous=True,
        scope=NodeScope.GLOBAL,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# CD - CHANGE DIR
# ----------------------------------

system.add(
    Node(
        key="cd",
        run=cd,
        anonymous=True,
        scope=NodeScope.GLOBAL,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# PWD - PRINT WORKING DIRECORY
# ----------------------------------

system.add(
    Node(
        key="pwd",
        run=pwd,
        anonymous=True,
        scope=NodeScope.GLOBAL,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# CLEAR - CLEAR VIEWPORT
# ----------------------------------

system.add(
    Node(
        key="clear",
        run=clear,
        anonymous=True,
        scope=NodeScope.GLOBAL,
        resolvable=True,
        navigable=False,
    )
)
