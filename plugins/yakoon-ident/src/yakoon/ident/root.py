from yakoon.base.nodes import Node

from .actors import group, membership, user
from .resources import get_resource
from .setup import on_setup

# ----------------------------------
# IDENT NODE
# ----------------------------------

ident = Node(
    key="ident",
    name="Ident",
    anonymous=True,
    on_setup=on_setup,
    on_resource=get_resource,
)

# ----------------------------------
# ADD MODELS
# ----------------------------------

ident.mount(user)
ident.mount(group)
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
    )
)

# ----------------------------------
# GRANT - DEFINE ACCESS PRIVILEGES
# ----------------------------------

ident.add(
    Node(
        key="grant",
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)
