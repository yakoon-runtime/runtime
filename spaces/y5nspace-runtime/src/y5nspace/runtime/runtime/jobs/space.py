from y5n.api.invocations import Invocation
from y5n.api.nodes import Node, NodeScope

from .bg import run as bg
from .fg import run as fg
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
    resolvable=True,
    run=list,
    scope=NodeScope.GLOBAL,
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


# ----------------------------------
# FOREGROUND
# ----------------------------------

jobs.add(
    Node(
        key=":fg",
        run=fg,
        anonymous=True,
        resolvable=True,
        navigable=False,
        scope=NodeScope.GLOBAL,
        invocations=[
            Invocation(args=["index"], default=True),
        ],
    )
)


# ----------------------------------
# BACKGROUND
# ----------------------------------

jobs.add(
    Node(
        key=":bg",
        run=bg,
        anonymous=True,
        resolvable=True,
        navigable=False,
        scope=NodeScope.GLOBAL,
    )
)
