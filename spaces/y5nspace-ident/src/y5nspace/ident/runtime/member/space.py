from y5n.base.nodes import Invocation, Node

from .membership_add import run as membership_add
from .membership_groups import run as membership_groups
from .membership_remove import run as membership_remove
from .membership_users import run as membership_users

# ----------------------------------
# MEMBERSHIP
# ----------------------------------

membership = Node(
    key="joins",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=membership_users,
    invocations=[
        Invocation(action=None, default=True),
    ],
)

# ----------------------------------
# ADD
# ----------------------------------

membership.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=membership_add,
        invocations=[Invocation(args=["username", "groupname"])],
    ),
)

# ----------------------------------
# USERS (LIST BY GROUPS)
# ----------------------------------

membership.add(
    Node(
        key="users",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=membership_users,
        invocations=[Invocation(args=["groupname"])],
    ),
)

# ----------------------------------
# GROUPS (LIST BY USERS)
# ----------------------------------

membership.add(
    Node(
        key="groups",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=membership_groups,
        invocations=[Invocation(args=["username"])],
    ),
)

# ----------------------------------
# REMOVE
# ----------------------------------

membership.add(
    Node(
        key="remove",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=membership_remove,
        invocations=[Invocation(args=["username", "groupname"])],
    ),
)
