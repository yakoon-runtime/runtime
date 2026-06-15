from y5n.api.nodes import Node, NodeScope

from .list import run as list

# ----------------------------------
# SESSION  (router)
# ----------------------------------


async def run(space):
    async for item in list(space):
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
