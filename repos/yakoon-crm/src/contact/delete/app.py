from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import CONTACT_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    name = space.request.arg(0)
    if not name:
        yield out_text("Error: contact name is required.")
        return

    contacts = space.ports.get(CONTACT_SERVICE)
    ns = space.ports.get(NAMESPACES).contact_namespace()

    try:
        await contacts.delete_contact(namespace=ns, name=name)
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Contact '{name}' deleted.")
