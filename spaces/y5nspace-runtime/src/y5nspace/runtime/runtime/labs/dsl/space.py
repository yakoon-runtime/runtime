from y5n.api.nodes import Node

from .delay import run as delay
from .out import run as out
from .receive import run as receive
from .send import run as send

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
# DELAY
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

# ----------------------------------
# SEND
# ----------------------------------

dsl.add(
    Node(
        key="send",
        run=send,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)


# ----------------------------------
# RECEIVE
# ----------------------------------

dsl.add(
    Node(
        key="receive",
        run=receive,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)
