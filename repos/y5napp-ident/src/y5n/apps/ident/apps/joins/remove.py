from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    username = req.arg(0)
    groupname = req.arg(1)

    ns_svc = ports.get("ident.namespaces")
    users_svc = ports.get("ident.users")
    groups_svc = ports.get("ident.groups")
    joins_svc = ports.get("ident.joins")

    user = await users_svc.get_by_username(
        namespace=await ns_svc.user_namespace(),
        username=username,
    )
    if not user:
        await io.write(f"User '{username}' not found.")
        return

    group = await groups_svc.get_by_name(
        namespace=await ns_svc.group_namespace(),
        name=groupname,
    )
    if not group:
        await io.write(f"Group '{groupname}' not found.")
        return

    join_obj = await joins_svc.remove_join(
        namespace=await ns_svc.join_namespace(),
        user_key=user.key,
        group_key=group.key,
    )

    doc = ports.get("document")
    result = await doc.render(name="default", state={"join": join_obj})
    await io.write(result)
