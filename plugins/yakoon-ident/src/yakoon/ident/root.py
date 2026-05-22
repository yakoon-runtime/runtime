from yakoon.base.nodes import Node

from .actors import user
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
# USERS
# ----------------------------------

ident.mount(user)


# ----------------------------------
# GROUPS
# ----------------------------------

ident.add(
    Node(
        key="group",
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# MEMBERSHIP
# ----------------------------------

ident.add(
    Node(
        key="membership",
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)

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
