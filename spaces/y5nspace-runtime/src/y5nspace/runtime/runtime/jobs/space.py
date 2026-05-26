from y5n.api.invocations import Invocation
from y5n.api.nodes import Node, NodeScope

from .list import run as list
from .setup import setup
from .stop import run as stop

# ----------------------------------
# JOBS
# ----------------------------------

jobs = Node(
    key="jobs",
    setup=setup,
    anonymous=True,
    navigable=True,
    resolvable=False,
    scope=NodeScope.NODE,
)

# ----------------------------------
# LIST
# ----------------------------------

jobs.add(
    Node(
        key="list",
        run=list,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)


# ----------------------------------
# STOP
# ----------------------------------

jobs.add(
    Node(
        key="stop",
        run=stop,
        anonymous=True,
        resolvable=True,
        navigable=False,
        invocations=[
            Invocation(args=["index"], default=True),
        ],
    )
)
