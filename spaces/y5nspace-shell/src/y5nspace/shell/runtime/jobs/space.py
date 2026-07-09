from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node, NodeScope

from .bg import run as bg
from .fg import run as fg
from .list import run as list
from .setup import setup
from .stop import run as stop

# ----------------------------------
# JOBS  (router)
# ----------------------------------


async def run(space):
    if space.request.has_option("stop"):
        async for item in stop(space):
            yield item
    elif space.request.has_option("fg"):
        async for item in fg(space):
            yield item
    elif space.request.has_option("bg"):
        async for item in bg(space):
            yield item
    else:
        async for item in list(space):
            yield item


jobs = Node(
    key="jobs",
    setup=setup,
    anonymous=True,
    navigable=True,
    resolvable=True,
    run=run,
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
            Invocation(
                params=[
                    Param(key="index", required=False, positional=True),
                    Param(key="current", required=False, positional=False),
                ],
                default=True,
            ),
        ],
    )
)


# ----------------------------------
# FOREGROUND
# ----------------------------------

jobs.add(
    Node(
        key="fg",
        run=fg,
        anonymous=True,
        resolvable=True,
        navigable=False,
        invocations=[
            Invocation(
                params=[Param(key="index", required=True, positional=True)],
                default=True,
            ),
        ],
    )
)


# ----------------------------------
# BACKGROUND
# ----------------------------------

jobs.add(
    Node(
        key="bg",
        run=bg,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)
