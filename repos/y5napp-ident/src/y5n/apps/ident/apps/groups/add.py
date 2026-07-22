from y5n.sdk import context, io, ports


async def main():

    req = context.request()
    name = req.arg(0)

    ns_svc = ports.get("ident.namespaces")
    namespace = await ns_svc.group_namespace()

    groups_svc = ports.get("ident.groups")
    group = await groups_svc.add_group(
        namespace=namespace,
        name=name,
    )

    doc = ports.get("document")
    result = await doc.render(
        name="default",
        state={"group": group},
    )

    await io.write(result)
