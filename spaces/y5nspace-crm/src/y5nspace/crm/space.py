from y5n.api.invocations import Invocation
from y5n.api.nodes import Node

from .runtime import (
    contact_add,
    contact_delete,
    contact_edit,
    contact_find,
    contact_list,
    contact_show,
    setup,
)

# ----------------------------------
# CRM
# ----------------------------------

crm = Node(
    key="crm",
    name="CRM",
    anonymous=True,
    navigable=True,
    setup=setup,
)

# ----------------------------------
# CRM - LIST
# ----------------------------------

crm.add(
    Node(
        key="contact-list",
        name="Contact list",
        run=contact_list.run,
        anonymous=True,
    )
)

# ----------------------------------
# CRM - ADD
# ----------------------------------

crm.add(
    Node(
        key="contact-add",
        name="Contact add",
        run=contact_add.run,
        anonymous=True,
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
    )
)

# ----------------------------------
# CRM - SHOW
# ----------------------------------

crm.add(
    Node(
        key="contact-show",
        name="Contact show",
        run=contact_show.run,
        anonymous=True,
        invocations=[
            Invocation(args=["name"]),
        ],
    )
)

# ----------------------------------
# CRM - EDIT
# ----------------------------------

crm.add(
    Node(
        key="contact-edit",
        name="Contact edit",
        run=contact_edit.run,
        anonymous=True,
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
    )
)

# ----------------------------------
# CRM - FIND
# ----------------------------------

crm.add(
    Node(
        key="contact-find",
        name="Contact find",
        run=contact_find.run,
        anonymous=True,
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
    )
)

# ----------------------------------
# CRM - DELETE
# ----------------------------------

crm.add(
    Node(
        key="contact-delete",
        name="Contact delete",
        run=contact_delete.run,
        anonymous=True,
        invocations=[
            Invocation(args=["name"]),
        ],
    )
)
