from y5n.api.nodes import Node
from y5n.base.nodes.types import NodeScope

from .cmd import run as cmd
from .delay import run as delay
from .out import run as out
from .prompt import run as prompt
from .receive import run as receive
from .send import run as send
from .suspend import run as suspend
from .task import run as task

# ----------------------------------
# DSL
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
        scope=NodeScope.GLOBAL,
    )
)

# ----------------------------------
# CMD
# ----------------------------------

dsl.add(
    Node(
        key="cmd",
        run=cmd,
        anonymous=True,
        resolvable=True,
        scope=NodeScope.GLOBAL,
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

# ----------------------------------
# SUSPEND
# ----------------------------------

dsl.add(
    Node(
        key="suspend",
        run=suspend,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)


# ----------------------------------
# PROMPT
# ----------------------------------

dsl.add(
    Node(
        key="prompt",
        run=prompt,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# TASK
# ----------------------------------

dsl.add(
    Node(
        key="task",
        run=task,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)
