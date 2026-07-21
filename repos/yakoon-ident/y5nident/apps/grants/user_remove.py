from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    username = req.arg(0)
    permission_key = req.arg(1)

    ns_svc = ports.get("ident.namespaces")
    users_svc = ports.get("ident.users")
    permgrant_svc = ports.get("ident.permgrant")

    user = await users_svc.get_by_username(namespace=await ns_svc.user_namespace(), username=username)
    if not user:
        await io.write(f"User '{username}' does not exist.")
        return

    grant = await permgrant_svc.remove_grant(
        namespace=await ns_svc.permgrant_namespace(),
        subject_key=user.key, permission_key=permission_key,
    )
    doc = ports.get("document")
    result = await doc.render(name="default", state={"grant": grant})
    await io.write(result)
