from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node
from y5n.api.runtime import Interaction

from .delete import run as exit_delete
from .edit import run as exit_edit
from .list import run as exit_list
from .show import run as exit_show

exit_node = Node(
    key="exit",
    name="Exit",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=exit_list,
    invocations=[
        Invocation(
            action=None,
            default=True,
            params=[
                Param(key="world", required=True, positional=False),
                Param(key="box"),
            ],
        ),
    ],
)

exit_node.add(
    Node(
        key="list",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=exit_list,
        invocations=[
            Invocation(
                params=[
                    Param(key="world", required=True, positional=False),
                    Param(key="box"),
                ],
            ),
        ],
    ),
)

exit_node.add(
    Node(
        key="show",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=exit_show,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="world", required=True, positional=False),
                    Param(key="box", required=True, positional=False),
                ],
            ),
        ],
    ),
)

exit_node.add(
    Node(
        key="edit",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=exit_edit,
        interaction=Interaction.INHERIT,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="world", required=True, positional=False),
                    Param(key="box", required=True, positional=False),
                    Param(key="new-name"),
                    Param(key="description"),
                    Param(key="direction"),
                ],
            ),
        ],
    ),
)

exit_node.add(
    Node(
        key="delete",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=exit_delete,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="world", required=True, positional=False),
                    Param(key="box", required=True, positional=False),
                ],
            ),
        ],
    ),
)
