from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .add import run as user_add
from .delete import run as user_delete
from .edit import run as user_edit
from .list import run as user_list

# ----------------------------------
# USER
# ----------------------------------

user = Node(
    key="users",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=user_list,
    invocations=[
        Invocation(action=None, default=True),
    ],
)

# ----------------------------------
# LIST
# ----------------------------------

user.add(
    Node(
        key="list",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=user_list,
    ),
)

# ----------------------------------
# ADD
# ----------------------------------

user.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=user_add,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="password"),
                ]
            ),
        ],
    ),
)

# ----------------------------------
# EDIT
# ----------------------------------

user.add(
    Node(
        key="edit",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=user_edit,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="password"),
                    Param(key="enabled"),
                ],
            ),
        ],
    ),
)

# ----------------------------------
# DELETE
# ----------------------------------

user.add(
    Node(
        key="delete",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=user_delete,
        invocations=[
            Invocation(params=[Param(key="name", required=True, positional=True)])
        ],
    ),
)
