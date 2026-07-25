from y5n.sdk import io, ports


async def main():
    contacts = ports.get("crm.contact.service")
    ns = ports.get("crm.namespaces")
    namespace = await ns.contact_namespace()
    all_contacts = await contacts.list_contacts(namespace=namespace)

    if not all_contacts:
        await io.write("No contacts.")
        return

    lines = ["Contacts:"]
    for c in all_contacts:
        parts = [f"  {c.data.name}"]
        if c.data.company:
            parts.append(f" - {c.data.company}")
        lines.append("".join(parts))
    await io.write("\n".join(lines))
