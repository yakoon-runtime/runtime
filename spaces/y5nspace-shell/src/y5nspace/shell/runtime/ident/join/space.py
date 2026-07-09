from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .add import run as join_add
from .groups import run as join_groups
from .remove import run as join_remove
from .users import run as join_users

# ----------------------------------
# JOINS
# ----------------------------------

join_node = Node(
    key="joins",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=join_users,
    invocations=[
        Invocation(action=None, default=True),
    ],
)

# ----------------------------------
# ADD
# ----------------------------------

join_node.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=join_add,
        invocations=[
            Invocation(
                params=[
                    Param(key="user", required=True, positional=True),
                    Param(key="group", required=True, positional=True),
                ]
            )
        ],
    ),
)

# ----------------------------------
# USERS (LIST BY GROUPS)
# ----------------------------------

join_node.add(
    Node(
        key="users",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=join_users,
        invocations=[
            Invocation(params=[Param(key="group", required=True, positional=True)])
        ],
    ),
)

# ----------------------------------
# GROUPS (LIST BY USERS)
# ----------------------------------

join_node.add(
    Node(
        key="groups",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=join_groups,
        invocations=[
            Invocation(params=[Param(key="user", required=True, positional=True)])
        ],
    ),
)

# ----------------------------------
# REMOVE
# ----------------------------------

join_node.add(
    Node(
        key="remove",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=join_remove,
        invocations=[
            Invocation(
                params=[
                    Param(key="user", required=True, positional=True),
                    Param(key="group", required=True, positional=True),
                ]
            )
        ],
    ),
)
