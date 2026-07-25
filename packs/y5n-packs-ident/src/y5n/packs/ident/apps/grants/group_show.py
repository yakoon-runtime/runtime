from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    groupname = req.arg(0)

    ns_svc = ports.get("ident.namespaces")
    groups_svc = ports.get("ident.groups")
    permgrant_svc = ports.get("ident.permgrant")

    group = await groups_svc.get_by_name(
        namespace=await ns_svc.group_namespace(), name=groupname
    )
    if not group:
        await io.write(f"Group '{groupname}' does not exist.")
        return

    grants = await permgrant_svc.list_subject_grants(
        namespace=await ns_svc.permgrant_namespace(),
        subject_key=group.key,
    )
    doc = ports.get("document")
    result = await doc.render(
        name="default", state={"grants": grants, "subject": groupname}
    )
    await io.write(result)
