from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node, NodeScope

from .connect import run as connect
from .list import run as list

# ----------------------------------
# NET
# ----------------------------------

net = Node(
    key="net",
    anonymous=True,
    navigable=True,
    resolvable=True,
    run=list,
    scope=NodeScope.GLOBAL,
)

# ----------------------------------
# LIST
# ----------------------------------

net.add(
    Node(
        key="list",
        run=list,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)


# ----------------------------------
# CONNECT
# ----------------------------------

net.add(
    Node(
        key="connect",
        run=connect,
        anonymous=True,
        resolvable=True,
        navigable=False,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                ],
            ),
        ],
    )
)
