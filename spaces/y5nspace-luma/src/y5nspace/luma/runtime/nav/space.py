from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node
from y5n.api.runtime import Interaction

from .connect import run as connect_run
from .dig import run as dig_run
from .drop import run as drop_run
from .enter import run as enter_run
from .entry import run as entry_run
from .go import run as go_run
from .inv import run as inv_run
from .leave import run as leave_run
from .look import run as look_run
from .move import run as move_run
from .place import run as place_run
from .take import run as take_run

# ----------------------------------
# LOOK
# ----------------------------------

look = Node(
    key="look",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=look_run,
)

# ----------------------------------
# GO
# ----------------------------------

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

# ----------------------------------
# DIG
# ----------------------------------

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

# ----------------------------------
# CONNECT
# ----------------------------------

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

# ----------------------------------
# ENTER
# ----------------------------------

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

# ----------------------------------
# ENTRY
# ----------------------------------

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

# ----------------------------------
# LEAVE
# ----------------------------------

leave = Node(
    key="leave",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=leave_run,
)

# ----------------------------------
# PLACE
# ----------------------------------

place = Node(
    key="place",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=place_run,
    invocations=[
        Invocation(
            params=[
                Param(key="name", required=True, positional=True),
                Param(key="description"),
                Param(key="box"),
            ],
        ),
    ],
)

# ----------------------------------
# MOVE
# ----------------------------------

move = Node(
    key="move",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=move_run,
    invocations=[
        Invocation(
            params=[
                Param(key="name", required=True, positional=True),
                Param(key="box", required=True, positional=False),
            ],
        ),
    ],
)

# ----------------------------------
# TAKE
# ----------------------------------

take = Node(
    key="take",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=take_run,
    invocations=[
        Invocation(
            params=[
                Param(key="name", required=True, positional=True),
            ],
        ),
    ],
)

# ----------------------------------
# DROP
# ----------------------------------

drop = Node(
    key="drop",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=drop_run,
    invocations=[
        Invocation(
            params=[
                Param(key="name", required=True, positional=True),
            ],
        ),
    ],
)

# ----------------------------------
# INVENTORY
# ----------------------------------

inv = Node(
    key="inv",
    anonymous=True,
    resolvable=True,
    navigable=False,
    run=inv_run,
)
