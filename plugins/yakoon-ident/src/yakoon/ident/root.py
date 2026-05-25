from __future__ import annotations

from yakoon.base.nodes import Invocation, Node, NodeScope

from .actors import grant, group, membership, on_setup, on_su, on_whoami, user

# ----------------------------------
# IDENT NODE
# ----------------------------------

ident = Node(
    key="ident",
    name="Ident",
    anonymous=True,
    on_setup=on_setup,
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
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_whoami,
        scope=NodeScope.GLOBAL,
    )
)

# ----------------------------------
# SU - SUBSITUTE USER
# ----------------------------------

ident.add(
    Node(
        key="su",
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_su,
        scope=NodeScope.GLOBAL,
        invocations=[
            Invocation(args=["user"], options=["password"]),
        ],
    )
)
