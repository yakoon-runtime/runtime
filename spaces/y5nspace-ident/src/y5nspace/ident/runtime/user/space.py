from y5n.base.nodes import Invocation, Node

from .user_add import run as user_add
from .user_delete import run as user_delete
from .user_edit import run as user_edit
from .user_list import run as user_list

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
            Invocation(args=["username"], options=["password"]),
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
            Invocation(args=["username"], options=["password", "enabled"]),
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
        invocations=[Invocation(args=["username"])],
    ),
)
