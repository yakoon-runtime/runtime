from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    username = req.arg(0)

    ns_svc = ports.get("ident.namespaces")
    users_svc = ports.get("ident.users")
    joins_svc = ports.get("ident.joins")

    user = await users_svc.get_by_username(
        namespace=await ns_svc.user_namespace(),
        username=username,
    )
    if not user:
        await io.write(f"User '{username}' not found.")
        return

    joins = await joins_svc.list_user_joins(
        namespace=await ns_svc.join_namespace(),
        user_key=user.key,
    )

    doc = ports.get("document")
    result = await doc.render(name="default", state={"joins": joins, "user": username})
    await io.write(result)
