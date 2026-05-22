from yakoon.base.nodes import Invocation, Node

from .on_group_add import on_group_add
from .on_group_delete import on_group_delete
from .on_group_edit import on_group_edit
from .on_group_list import on_group_list

# ----------------------------------
# GROUP
# ----------------------------------

group = Node(
    key="group",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    on_run=on_group_list,
    invocations=[
        Invocation(action=None, default=True),
    ],
)

# ----------------------------------
# LIST
# ----------------------------------

group.add(
    Node(
        key="list",
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_group_list,
    ),
)

# ----------------------------------
# ADD
# ----------------------------------

group.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_group_add,
        invocations=[
            Invocation(args=["groupname"]),
        ],
    ),
)

# ----------------------------------
# EDIT
# ----------------------------------

group.add(
    Node(
        key="edit",
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_group_edit,
        invocations=[
            Invocation(args=["groupname"], options=["enabled"]),
        ],
    ),
)

# ----------------------------------
# DELETE
# ----------------------------------

group.add(
    Node(
        key="delete",
        anonymous=True,
        resolvable=True,
        navigable=False,
        on_run=on_group_delete,
        invocations=[Invocation(args=["groupname"])],
    ),
)
