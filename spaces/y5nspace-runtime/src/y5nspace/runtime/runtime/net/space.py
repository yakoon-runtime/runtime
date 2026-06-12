from y5n.api.nodes import Node, NodeScope

from .connect import run as connect
from .list import run as list


async def run(space):
    if space.request.has_option("connect"):
        async for item in connect(space):
            yield item
    else:
        async for item in list(space):
            yield item


# ----------------------------------
# NET
# ----------------------------------

net = Node(
    key="net",
    anonymous=True,
    navigable=True,
    resolvable=True,
    run=run,
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
