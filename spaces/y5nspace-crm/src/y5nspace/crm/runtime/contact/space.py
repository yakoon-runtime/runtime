from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .add import run as contact_add
from .delete import run as contact_delete
from .edit import run as contact_edit
from .find import run as contact_find
from .list import run as contact_list
from .show import run as contact_show

# ----------------------------------
# CONTACT
# ----------------------------------

contacts = Node(
    key="contacts",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    run=contact_list,
    invocations=[
        Invocation(action=None, default=True),
    ],
)

# ----------------------------------
# LIST
# ----------------------------------

contacts.add(
    Node(
        key="list",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=contact_list,
    ),
)

# ----------------------------------
# ADD
# ----------------------------------

contacts.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=contact_add,
        invocations=[
            Invocation(
                args=[Param(key="name")],
                options=[
                    Param(key="company"),
                    Param(key="email"),
                    Param(key="phone"),
                    Param(key="street"),
                    Param(key="zip"),
                    Param(key="city"),
                    Param(key="country"),
                    Param(key="notes"),
                ],
            ),
        ],
    ),
)

# ----------------------------------
# SHOW
# ----------------------------------

contacts.add(
    Node(
        key="show",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=contact_show,
        invocations=[
            Invocation(args=[Param(key="name")]),
        ],
    ),
)

# ----------------------------------
# EDIT
# ----------------------------------

contacts.add(
    Node(
        key="edit",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=contact_edit,
        invocations=[
            Invocation(
                args=[Param(key="name")],
                options=[
                    Param(key="company"),
                    Param(key="email"),
                    Param(key="phone"),
                    Param(key="street"),
                    Param(key="zip"),
                    Param(key="city"),
                    Param(key="country"),
                    Param(key="notes"),
                ],
            ),
        ],
    ),
)

# ----------------------------------
# DELETE
# ----------------------------------

contacts.add(
    Node(
        key="delete",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=contact_delete,
        invocations=[
            Invocation(args=[Param(key="name")]),
        ],
    ),
)

# ----------------------------------
# FIND
# ----------------------------------

contacts.add(
    Node(
        key="find",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=contact_find,
        invocations=[
            Invocation(
                default=True,
                min_options=1,
                options=[
                    Param(key="name"),
                    Param(key="company"),
                    Param(key="email"),
                    Param(key="phone"),
                    Param(key="city"),
                    Param(key="country"),
                ],
            ),
        ],
    ),
)
