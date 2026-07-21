from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    groupname = req.arg(0)

    ns_svc = ports.get("ident.namespaces")
    groups_svc = ports.get("ident.groups")
    joins_svc = ports.get("ident.joins")

    group = await groups_svc.get_by_name(
        namespace=await ns_svc.group_namespace(),
        name=groupname,
    )
    if not group:
        await io.write(f"Group '{groupname}' not found.")
        return

    joins = await joins_svc.list_group_joins(
        namespace=await ns_svc.join_namespace(),
        group_key=group.key,
    )

    doc = ports.get("document")
    result = await doc.render(name="default", state={"joins": joins, "group": groupname})
    await io.write(result)
