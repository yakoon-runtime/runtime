from y5n.sdk import context, io, ports


async def main():

    req = context.request()
    name = req.arg(0)
    changes = {"enabled": req.option("enabled")}

    ns_svc = ports.get("ident.namespaces")
    namespace = await ns_svc.group_namespace()

    groups_svc = ports.get("ident.groups")
    group = await groups_svc.edit_group(
        namespace=namespace,
        name=name,
        changes=changes,
    )

    doc = ports.get("document")
    result = await doc.render(
        name="default",
        state={"group": group},
    )
    await io.write(result)
