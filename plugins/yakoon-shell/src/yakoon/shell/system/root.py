from yakoon.base.nodes import Node
from yakoon.base.nodes.invocation import Invocation
from yakoon.base.nodes.types import NodeScope

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
        on_run=on_welcome,
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
        on_run=on_version,
        anonymous=True,
        scope=NodeScope.NODE,
        resolvable=True,
        navigable=False,
        invocations=[
            Invocation(action="list"),
            Invocation(action="add", args=["groupname"]),
            Invocation(action="delete", args=["groupname"]),
            Invocation(action="edit", args=["groupname"], options=["enabled"]),
        ],
    )
)

# ----------------------------------
# MAN
# ----------------------------------

system.add(
    Node(
        key="man",
        on_run=on_man,
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
        on_run=on_list,
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
        on_run=on_cd,
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
        on_run=on_pwd,
        anonymous=True,
        scope=NodeScope.GLOBAL,
        resolvable=True,
        navigable=False,
    )
)
