from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import CONTACT_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    name = space.request.arg(0)
    if not name:
        yield out_text("Error: name is required.")
        return

    contacts = space.ports.get(CONTACT_SERVICE)
    ns = space.ports.get(NAMESPACES).contact_namespace()

    try:
        contact = await contacts.add_contact(
            namespace=ns,
            name=name,
            company=space.request.option("company") or "",
            email=space.request.option("email") or "",
            phone=space.request.option("phone") or "",
            street=space.request.option("street") or "",
            zip=space.request.option("zip") or "",
            city=space.request.option("city") or "",
            country=space.request.option("country") or "",
            notes=space.request.option("notes") or "",
        )
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Contact '{contact.data.name}' created.")
