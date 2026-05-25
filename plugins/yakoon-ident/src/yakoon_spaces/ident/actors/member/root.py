from yakoon.base.nodes import Invocation, Node

from .on_membership_add import on_membership_add
from .on_membership_groups import on_membership_groups
from .on_membership_remove import on_membership_remove
from .on_membership_users import on_membership_users

# ----------------------------------
# MEMBERSHIP
# ----------------------------------

membership = Node(
    key="membership",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=on_membership_users,
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
        run=on_membership_add,
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
        run=on_membership_users,
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
        run=on_membership_groups,
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
        run=on_membership_remove,
        invocations=[Invocation(args=["username", "groupname"])],
    ),
)
