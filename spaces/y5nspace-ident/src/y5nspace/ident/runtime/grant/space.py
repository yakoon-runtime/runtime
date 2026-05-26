from y5n.base.nodes import Invocation, Node

from .grant_add import run as grant_add
from .grant_group import run as grant_group
from .grant_perm import run as grant_perm
from .grant_remove import run as grant_remove
from .grant_user import run as grant_user
from .setup import setup

# ----------------------------------
# MEMBERSHIP
# ----------------------------------

grant = Node(
    key="grants",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    setup=setup,
    run=grant_user,
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
        run=grant_add,
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
        run=grant_remove,
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
        run=grant_user,
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
        run=grant_group,
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
        run=grant_perm,
        invocations=[Invocation(args=["permission"])],
    ),
)
