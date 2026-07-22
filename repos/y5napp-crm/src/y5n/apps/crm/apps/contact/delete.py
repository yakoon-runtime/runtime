from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    name = req.arg(0)
    if not name:
        await io.write("Error: contact name is required.")
        return

    contacts = ports.get("crm.contact.service")
    ns = ports.get("crm.namespaces")
    namespace = await ns.contact_namespace()

    try:
        await contacts.delete_contact(namespace=namespace, name=name)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Contact '{name}' deleted.")
