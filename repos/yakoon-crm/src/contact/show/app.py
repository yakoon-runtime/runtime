from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import CONTACT_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    name = space.request.arg(0)
    if not name:
        yield out_text("Show which contact?")
        return

    contacts = space.ports.get(CONTACT_SERVICE)
    ns = space.ports.get(NAMESPACES).contact_namespace()
    contact = await contacts.get_by_name(namespace=ns, name=name)

    if contact is None:
        yield out_text(f"Contact not found: {name}")
        return

    d = contact.data
    lines = [f"Contact: {d.name}"]
    for label, val in [("Company", d.company), ("Email", d.email), ("Phone", d.phone),
                        ("Street", d.street), ("Zip", d.zip), ("City", d.city),
                        ("Country", d.country), ("Notes", d.notes)]:
        if val:
            lines.append(f"  {label}: {val}")
    yield out_text("\n".join(lines))
