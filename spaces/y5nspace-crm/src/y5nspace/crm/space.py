from y5n.api.nodes import Node

from .runtime import contacts, setup

# ----------------------------------
# CRM
# ----------------------------------

crm = Node(
    key="crm",
    name="CRM",
    anonymous=True,
    setup=setup,
)

# ----------------------------------
# MOUNT CONTACTS
# ----------------------------------

crm.mount(contacts)
