from y5n.api.nodes import Node

from .delay import run as delay
from .out import run as out

# ----------------------------------
# LABS
# ----------------------------------

dsl = Node(
    key="dsl",
    anonymous=True,
    navigable=True,
    resolvable=False,
)

# ----------------------------------
# OUT
# ----------------------------------

dsl.add(
    Node(
        key="out",
        run=out,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# delay
# ----------------------------------

dsl.add(
    Node(
        key="delay",
        run=delay,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)
