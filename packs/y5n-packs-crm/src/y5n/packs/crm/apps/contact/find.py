from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    contacts = ports.get("crm.contact.service")
    ns = ports.get("crm.namespaces")
    namespace = await ns.contact_namespace()

    filters = {}
    for field in ("name", "company", "email", "phone", "city", "country"):
        val = req.option(field)
        if val:
            filters[field] = val

    all_contacts = await contacts.find_contacts(namespace=namespace, **filters)

    if not all_contacts:
        await io.write("No contacts found.")
        return

    lines = ["Contacts:"]
    for c in all_contacts:
        parts = [f"  {c.data.name}"]
        if c.data.company:
            parts.append(f" - {c.data.company}")
        lines.append("".join(parts))
    await io.write("\n".join(lines))
