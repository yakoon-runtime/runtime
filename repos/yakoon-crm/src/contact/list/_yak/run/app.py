from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import CONTACT_SERVICE, NAMESPACES


async def run(space: NodeSpace):
    contacts = space.ports.get(CONTACT_SERVICE)
    ns = space.ports.get(NAMESPACES).contact_namespace()
    all_contacts = await contacts.list_contacts(namespace=ns)

    if not all_contacts:
        yield out_text("No contacts.")
        return

    lines = ["Contacts:"]
    for c in all_contacts:
        parts = [f"  {c.data.name}"]
        if c.data.company:
            parts.append(f" - {c.data.company}")
        lines.append("".join(parts))
    yield out_text("\n".join(lines))
