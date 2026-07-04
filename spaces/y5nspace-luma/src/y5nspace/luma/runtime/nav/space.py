from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node
from y5n.api.runtime import Interaction

from .connect import run as connect_run
from .dig import run as dig_run
from .enter import run as enter_run
from .entry import run as entry_run
from .go import run as go_run
from .leave import run as leave_run
from .look import run as look_run

look = Node(
    key="look",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=look_run,
)

go = Node(
    key="go",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=go_run,
    invocations=[
        Invocation(
            params=[
                Param(key="direction", required=True, positional=True),
            ],
        ),
    ],
)

dig = Node(
    key="dig",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=dig_run,
    interaction=Interaction.INHERIT,
    invocations=[
        Invocation(
            params=[
                Param(key="name", required=True, positional=True),
                Param(key="direction"),
                Param(key="via"),
                Param(key="twoway"),
            ],
        ),
    ],
)

connect = Node(
    key="connect",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=connect_run,
    invocations=[
        Invocation(
            params=[
                Param(key="name", required=True, positional=True),
                Param(key="direction"),
                Param(key="via"),
                Param(key="twoway"),
            ],
        ),
    ],
)

enter = Node(
    key="enter",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=enter_run,
    invocations=[
        Invocation(
            params=[
                Param(key="world", required=True, positional=True),
                Param(key="box"),
            ],
        ),
    ],
)

entry = Node(
    key="entry",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=entry_run,
    invocations=[
        Invocation(
            params=[
                Param(key="world", required=True, positional=True),
                Param(key="box"),
            ],
        ),
    ],
)

leave = Node(
    key="leave",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=leave_run,
)
