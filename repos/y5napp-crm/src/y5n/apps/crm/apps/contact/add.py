from y5n.sdk import context, io, ports


async def main():

    req = context.request()
    name = req.arg(0)
    contacts = ports.get("crm.contact.service")
    ns = ports.get("crm.namespaces")
    namespace = await ns.contact_namespace()

    try:
        await contacts.add_contact(
            namespace=namespace,
            name=name,
            company=req.option("company") or "",
            email=req.option("email") or "",
            phone=req.option("phone") or "",
            street=req.option("street") or "",
            zip=req.option("zip") or "",
            city=req.option("city") or "",
            country=req.option("country") or "",
            notes=req.option("notes") or "",
        )
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Contact '{name}' created.")
