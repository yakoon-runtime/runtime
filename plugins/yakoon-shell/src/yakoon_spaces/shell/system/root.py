from yakoon.api.invocations import Invocation
from yakoon.api.nodes import Node, NodeScope

from .on_cd import on_cd
from .on_list import on_list
from .on_man import on_man
from .on_pwd import on_pwd
from .on_version import on_version
from .on_welcome import on_welcome

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
# WELCOME
# ----------------------------------

system.add(
    Node(
        key="welcome",
        run=on_welcome,
        anonymous=True,
        scope=NodeScope.NODE,
        resolvable=True,
        navigable=True,
    )
)

# ----------------------------------
# VERSION
# ----------------------------------

system.add(
    Node(
        key="version",
        run=on_version,
        anonymous=True,
        scope=NodeScope.NODE,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# MAN
# ----------------------------------

system.add(
    Node(
        key="man",
        run=on_man,
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
        run=on_list,
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
        run=on_cd,
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
        run=on_pwd,
        anonymous=True,
        scope=NodeScope.GLOBAL,
        resolvable=True,
        navigable=False,
    )
)
