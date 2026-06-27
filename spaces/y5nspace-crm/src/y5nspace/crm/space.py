from y5n.api.nodes import Node

from .runtime import contact_add, contact_delete, contact_edit, contact_list, contact_show, setup

crm = Node(
    key="crm",
    name="CRM",
    anonymous=True,
    navigable=True,
    setup=setup,
)

crm.add(Node(
    key="contact-list",
    name="Contact list",
    run=contact_list.run,
))
crm.add(Node(
    key="contact-add",
    name="Contact add",
    run=contact_add.run,
))
crm.add(Node(
    key="contact-show",
    name="Contact show",
    run=contact_show.run,
))
crm.add(Node(
    key="contact-edit",
    name="Contact edit",
    run=contact_edit.run,
))
crm.add(Node(
    key="contact-delete",
    name="Contact delete",
    run=contact_delete.run,
))
