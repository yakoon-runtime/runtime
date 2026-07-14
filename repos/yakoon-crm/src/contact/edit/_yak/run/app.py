from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import CONTACT_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    name = space.request.arg(0)
    if not name:
        yield out_text("Error: contact name is required.")
        return

    contacts = space.ports.get(CONTACT_SERVICE)
    ns = space.ports.get(NAMESPACES).contact_namespace()
    contact = await contacts.get_by_name(namespace=ns, name=name)

    if contact is None:
        yield out_text(f"Contact not found: {name}")
        return

    changes = {}
    for field in ("company", "email", "phone", "street", "zip", "city", "country", "notes"):
        val = space.request.option(field)
        if val is not None:
            changes[field] = val

    if not changes:
        yield out_text("No changes provided.")
        return

    try:
        await contacts.edit_contact(namespace=ns, name=name, changes=changes)
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Contact '{name}' updated.")
