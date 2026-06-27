from y5n.api.invocations import Invocation
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
                args=["name"],
                options=[
                    "company",
                    "email",
                    "phone",
                    "street",
                    "zip",
                    "city",
                    "country",
                    "notes",
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
            Invocation(args=["name"]),
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
                args=["name"],
                options=[
                    "company",
                    "email",
                    "phone",
                    "street",
                    "zip",
                    "city",
                    "country",
                    "notes",
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
            Invocation(args=["name"]),
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
                    "name",
                    "company",
                    "email",
                    "phone",
                    "city",
                    "country",
                ],
            ),
        ],
    ),
)
