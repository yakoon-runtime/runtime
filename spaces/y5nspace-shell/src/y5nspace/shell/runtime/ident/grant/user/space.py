from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .add import run as user_add
from .remove import run as user_remove
from .show import run as user_show

# ----------------------------------
# USER GRANTS
# ----------------------------------

user = Node(
    key="user",
    anonymous=True,
    resolvable=False,
    navigable=True,
    contextual=True,
)

user.add(
    Node(
        key="show",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=user_show,
        invocations=[
            Invocation(
                params=[Param(key="name", required=True, positional=True)],
            ),
        ],
    ),
)

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
                    Param(key="permission", required=True, positional=True),
                    Param(key="bits"),
                    Param(key="deny"),
                ],
            ),
        ],
    ),
)

user.add(
    Node(
        key="remove",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=user_remove,
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
