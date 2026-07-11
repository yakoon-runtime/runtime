from __future__ import annotations

from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .grant.space import grant
from .group.space import group
from .join.space import join_node
from .setup import setup
from .su import run as su
from .user.space import user
from .whoami import run as whoami

# ----------------------------------
# IDENTITY NODE
# ----------------------------------

ident = Node(
    key="ident",
    name="Identity",
    anonymous=True,
    resolvable=False,
    navigable=True,
    setup=setup,
)

# ----------------------------------
# MOUNT TREES
# ----------------------------------

ident.mount(user)
ident.mount(group)
ident.mount(grant)
ident.mount(join_node)

# ----------------------------------
# WHOAMI
# ----------------------------------

ident.add(
    Node(
        key="whoami",
        anonymous=True,  # GLOBAL
        resolvable=True,
        navigable=False,
        run=whoami,
    )
)

# ----------------------------------
# SU - SUBSITUTE USER
# ----------------------------------

ident.add(
    Node(
        key="su",
        anonymous=True,  # GLOBAL
        resolvable=True,
        navigable=False,
        run=su,

        invocations=[
            Invocation(
                params=[
                    Param(key="user", positional=True),
                    Param(key="password"),
                ]
            ),
        ],
    )
)
