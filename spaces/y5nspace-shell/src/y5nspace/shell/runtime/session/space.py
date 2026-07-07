from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node, NodeScope

from .attach import run as attach
from .current import run as current
from .detach import run as detach
from .list import run as list

# ----------------------------------
# SESSION
# ----------------------------------

session = Node(
    key="session",
    anonymous=True,
    navigable=True,
    resolvable=True,
    run=list,
    scope=NodeScope.GLOBAL,
)

# ----------------------------------
# LIST
# ----------------------------------

session.add(
    Node(
        key="list",
        run=list,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# ATTACH
# ----------------------------------

session.add(
    Node(
        key="attach",
        run=attach,
        anonymous=True,
        resolvable=True,
        navigable=False,
        invocations=[
            Invocation(
                params=[
                    Param(key="key", required=True, positional=True),
                ],
            ),
        ],
    )
)

# ----------------------------------
# DETACH
# ----------------------------------

session.add(
    Node(
        key="detach",
        run=detach,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# CURRENT
# ----------------------------------

session.add(
    Node(
        key="current",
        run=current,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)
