from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node
from y5n.api.runtime import Interaction

from .add import run as note_add
from .delete import run as note_delete
from .edit import run as note_edit
from .inbox import run as note_inbox
from .list import run as note_list
from .put import run as note_put
from .remove import run as note_remove
from .show import run as note_show

note_node = Node(
    key="note",
    name="Note",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=note_list,
    invocations=[
        Invocation(action=None, default=True),
    ],
)

note_node.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=note_add,
        interaction=Interaction.INHERIT,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="content"),
                ],
            ),
        ],
    ),
)

note_node.add(
    Node(
        key="edit",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=note_edit,
        interaction=Interaction.INHERIT,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="new-name"),
                    Param(key="content"),
                ],
            ),
        ],
    ),
)

note_node.add(
    Node(
        key="delete",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=note_delete,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                ],
            ),
        ],
    ),
)

note_node.add(
    Node(
        key="list",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=note_list,
        invocations=[
            Invocation(
                params=[
                    Param(key="box"),
                    Param(key="world"),
                ],
            ),
        ],
    ),
)

note_node.add(
    Node(
        key="inbox",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=note_inbox,
    ),
)

note_node.add(
    Node(
        key="put",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=note_put,
        interaction=Interaction.INHERIT,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="box"),
                ],
            ),
        ],
    ),
)

note_node.add(
    Node(
        key="remove",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=note_remove,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="box"),
                ],
            ),
        ],
    ),
)

note_node.add(
    Node(
        key="show",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=note_show,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                ],
            ),
        ],
    ),
)
