from y5n.api.nodes import Node, NodeScope

from .attach import run as attach
from .current import run as current
from .detach import run as detach
from .list import run as list

# ----------------------------------
# SESSION  (router)
# ----------------------------------


async def run(space):
    if space.request.has_option("attach"):
        async for item in attach(space):
            yield item
    elif space.request.has_option("detach"):
        async for item in detach(space):
            yield item
    elif space.request.has_option("list"):
        async for item in list(space):
            yield item
    else:
        async for item in current(space):
            yield item


session = Node(
    key="session",
    anonymous=True,
    navigable=True,
    resolvable=True,
    run=run,
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

