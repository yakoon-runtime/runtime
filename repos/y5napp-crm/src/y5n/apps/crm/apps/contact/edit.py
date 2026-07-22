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

    changes = {}
    for field in (
        "company",
        "email",
        "phone",
        "street",
        "zip",
        "city",
        "country",
        "notes",
    ):
        val = req.option(field)
        if val is not None:
            changes[field] = val

    if not changes:
        await io.write("No changes provided.")
        return

    try:
        await contacts.edit_contact(namespace=namespace, name=name, changes=changes)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Contact '{name}' updated.")
