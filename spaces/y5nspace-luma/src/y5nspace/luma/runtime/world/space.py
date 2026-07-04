from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node
from y5n.api.runtime import Interaction

from .add import run as world_add
from .delete import run as world_delete
from .edit import run as world_edit
from .list import run as world_list
from .show import run as world_show

# ----------------------------------
# WORLD
# ----------------------------------

world = Node(
    key="world",
    name="World",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=world_list,
    invocations=[
        Invocation(action=None, default=True),
    ],
)

# ----------------------------------
# LIST
# ----------------------------------

world.add(
    Node(
        key="list",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=world_list,
    ),
)

# ----------------------------------
# ADD
# ----------------------------------

world.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        interaction=Interaction.INHERIT,
        run=world_add,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="description"),
                ],
            ),
        ],
    ),
)

# ----------------------------------
# SHOW
# ----------------------------------

world.add(
    Node(
        key="show",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=world_show,
        invocations=[
            Invocation(params=[Param(key="name", required=True, positional=True)]),
        ],
    ),
)

# ----------------------------------
# EDIT
# ----------------------------------

world.add(
    Node(
        key="edit",
        anonymous=True,
        resolvable=True,
        navigable=False,
        interaction=Interaction.INHERIT,
        run=world_edit,
        invocations=[
            Invocation(
                params=[
                    Param(key="name", required=True, positional=True),
                    Param(key="new-name"),
                    Param(key="description"),
                ],
            ),
        ],
    ),
)

# ----------------------------------
# DELETE
# ----------------------------------

world.add(
    Node(
        key="delete",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=world_delete,
        invocations=[
            Invocation(params=[Param(key="name", required=True, positional=True)]),
        ],
    ),
)
