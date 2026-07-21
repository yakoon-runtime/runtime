from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    groupname = req.arg(0)
    permission_key = req.arg(1)

    ns_svc = ports.get("ident.namespaces")
    groups_svc = ports.get("ident.groups")
    permgrant_svc = ports.get("ident.permgrant")

    group = await groups_svc.get_by_name(namespace=await ns_svc.group_namespace(), name=groupname)
    if not group:
        await io.write(f"Group '{groupname}' does not exist.")
        return

    grant = await permgrant_svc.remove_grant(
        namespace=await ns_svc.permgrant_namespace(),
        subject_key=group.key, permission_key=permission_key,
    )
    doc = ports.get("document")
    result = await doc.render(name="default", state={"grant": grant})
    await io.write(result)
