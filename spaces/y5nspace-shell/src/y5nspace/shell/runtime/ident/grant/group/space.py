from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .add import run as group_add
from .remove import run as group_remove
from .show import run as group_show

# ----------------------------------
# GROUP GRANTS
# ----------------------------------

group = Node(
    key="group",
    anonymous=True,
    resolvable=False,
    navigable=True,
    contextual=True,
)

group.add(
    Node(
        key="show",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=group_show,
        invocations=[
            Invocation(
                params=[Param(key="name", required=True, positional=True)],
            ),
        ],
    ),
)

group.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=group_add,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="permission", required=True, positional=True),
                    Param(key="bits"),
                    Param(key="deny"),
                ],
            ),
        ],
    ),
)

group.add(
    Node(
        key="remove",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=group_remove,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="permission", required=True, positional=True),
                ],
            ),
        ],
    ),
)
