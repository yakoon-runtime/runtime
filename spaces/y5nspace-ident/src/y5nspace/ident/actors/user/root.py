from y5n.base.nodes import Invocation, Node

from .on_user_add import on_user_add
from .on_user_delete import on_user_delete
from .on_user_edit import on_user_edit
from .on_user_list import on_user_list

# ----------------------------------
# USER
# ----------------------------------

user = Node(
    key="user",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=on_user_list,
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
        run=on_user_list,
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
        run=on_user_add,
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
        run=on_user_edit,
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
        run=on_user_delete,
        invocations=[Invocation(args=["username"])],
    ),
)
