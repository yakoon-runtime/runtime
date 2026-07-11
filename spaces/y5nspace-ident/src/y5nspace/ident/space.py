from __future__ import annotations

from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .runtime.grant.space import grant
from .runtime.group.space import group
from .runtime.member.space import membership
from .runtime.setup import setup
from .runtime.su import run as su
from .runtime.user.space import user
from .runtime.whoami import run as whoami

# ----------------------------------
# IDENT NODE
# ----------------------------------

ident = Node(
    key="ident",
    name="Ident",
    anonymous=True,
    setup=setup,
)

# ----------------------------------
# MOUNT TREES
# ----------------------------------

ident.mount(user)
ident.mount(group)
ident.mount(grant)
ident.mount(membership)

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
