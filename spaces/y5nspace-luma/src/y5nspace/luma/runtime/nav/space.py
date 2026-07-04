from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .enter import run as enter_run
from .entry import run as entry_run
from .leave import run as leave_run

enter = Node(
    key="enter",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=enter_run,
    invocations=[
        Invocation(
            params=[
                Param(key="name", required=True, positional=True),
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
                Param(key="name", required=True, positional=True),
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
