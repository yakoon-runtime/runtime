from yakoon.base.nodes import Invocation, Node

from .on_grant_add import on_grant_add
from .on_grant_group import on_grant_group
from .on_grant_perm import on_grant_perm
from .on_grant_remove import on_grant_remove
from .on_grant_user import on_grant_user
from .on_setup import on_setup

# ----------------------------------
# MEMBERSHIP
# ----------------------------------

grant = Node(
    key="grant",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    on_setup=on_setup,
    on_run=on_grant_user,
    invocations=[
        Invocation(action="user", args=["username"]),
    ],
)


# ----------------------------------
# ADD
# ----------------------------------

grant.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_grant_add,
        invocations=[
            Invocation(args=["type", "name", "permission"], options=["bits", "deny"]),
        ],
    ),
)

# ----------------------------------
# REMOVE
# ----------------------------------

grant.add(
    Node(
        key="remove",
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_grant_remove,
        invocations=[Invocation(args=["type", "name", "permission"])],
    ),
)


# ----------------------------------
# USER
# ----------------------------------

grant.add(
    Node(
        key="user",
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_grant_user,
        invocations=[
            Invocation(action="user", args=["username"]),
        ],
    ),
)

# ----------------------------------
# GROUP
# ----------------------------------

grant.add(
    Node(
        key="group",
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_grant_group,
        invocations=[Invocation(args=["groupname"])],
    ),
)

# ----------------------------------
# PERMISSION
# ----------------------------------

grant.add(
    Node(
        key="permission",
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_grant_perm,
        invocations=[Invocation(args=["permission"])],
    ),
)
