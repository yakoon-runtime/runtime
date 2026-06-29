from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .group_add import run as group_add
from .group_delete import run as group_delete
from .group_edit import run as group_edit
from .group_list import run as group_list

# ----------------------------------
# GROUP
# ----------------------------------

group = Node(
    key="groups",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=group_list,
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
        run=group_list,
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
        run=group_add,
        invocations=[
            Invocation(args=[Param(key="groupname")]),
        ],
    ),
)

group.add(
    Node(
        key="edit",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=group_edit,
        invocations=[
            Invocation(args=[Param(key="groupname")], options=[Param(key="enabled")]),
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
        run=group_delete,
        invocations=[Invocation(args=[Param(key="groupname")])],
    ),
)
