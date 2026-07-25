from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    name = req.arg(0)
    contacts = ports.get("crm.contact.service")
    ns = ports.get("crm.namespaces")
    namespace = await ns.contact_namespace()
    contact = await contacts.get_by_name(namespace=namespace, name=name)

    if contact is None:
        await io.write(f"Contact not found: {name}")
        return

    d = contact.data
    lines = [f"Contact: {d.name}"]
    for label, val in [
        ("Company", d.company),
        ("Email", d.email),
        ("Phone", d.phone),
        ("Street", d.street),
        ("Zip", d.zip),
        ("City", d.city),
        ("Country", d.country),
        ("Notes", d.notes),
    ]:
        if val:
            lines.append(f"  {label}: {val}")
    await io.write("\n".join(lines))
