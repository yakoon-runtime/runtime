from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node
from y5n.api.runtime import Interaction

from .add import run as box_add
from .delete import run as box_delete
from .edit import run as box_edit
from .list import run as box_list
from .show import run as box_show

box = Node(
    key="box",
    name="Box",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=box_list,
    invocations=[
        Invocation(action=None, default=True),
    ],
)

box.add(
    Node(
        key="list",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=box_list,
        invocations=[
            Invocation(
                params=[
                    Param(key="world", required=True, positional=False),
                    Param(key="parent"),
                ],
            ),
        ],
    ),
)

box.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        interaction=Interaction.INHERIT,
        run=box_add,
        invocations=[
            Invocation(
                params=[
                    Param(key="world", required=True, positional=False),
                    Param(key="parent"),
                    Param(key="name", required=True, positional=True),
                    Param(key="description"),
                ],
            ),
        ],
    ),
)

box.add(
    Node(
        key="show",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=box_show,
        invocations=[
            Invocation(
                params=[Param(key="id", required=True, positional=True)],
            ),
        ],
    ),
)

box.add(
    Node(
        key="edit",
        anonymous=True,
        resolvable=True,
        navigable=False,
        interaction=Interaction.INHERIT,
        run=box_edit,
        invocations=[
            Invocation(
                params=[
                    Param(key="id", required=True, positional=True),
                    Param(key="name"),
                    Param(key="description"),
                ],
            ),
        ],
    ),
)

box.add(
    Node(
        key="delete",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=box_delete,
        invocations=[
            Invocation(params=[Param(key="id", required=True, positional=True)]),
        ],
    ),
)
