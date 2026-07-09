from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .show import run as permission_show

# ----------------------------------
# PERMISSION GRANTS
# ----------------------------------

permission = Node(
    key="permission",
    anonymous=True,
    resolvable=False,
    navigable=True,
    contextual=True,
)

permission.add(
    Node(
        key="show",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=permission_show,
        invocations=[
            Invocation(
                params=[Param(key="permission", required=True, positional=True)],
            ),
        ],
    ),
)
