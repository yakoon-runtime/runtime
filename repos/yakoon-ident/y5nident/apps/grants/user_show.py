from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    username = req.arg(0)

    ns_svc = ports.get("ident.namespaces")
    users_svc = ports.get("ident.users")
    permgrant_svc = ports.get("ident.permgrant")

    user = await users_svc.get_by_username(namespace=await ns_svc.user_namespace(), username=username)
    if not user:
        await io.write(f"User '{username}' does not exist.")
        return

    grants = await permgrant_svc.list_subject_grants(
        namespace=await ns_svc.permgrant_namespace(), subject_key=user.key,
    )
    doc = ports.get("document")
    result = await doc.render(name="default", state={"grants": grants, "subject": username})
    await io.write(result)
