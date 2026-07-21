from y5n.sdk import io, ports


async def main():
    ns_svc = ports.get("ident.namespaces")
    namespace = await ns_svc.group_namespace()

    groups_svc = ports.get("ident.groups")
    groups = await groups_svc.list_groups(namespace=namespace)

    doc = ports.get("document")
    result = await doc.render(
        name="default",
        state={"groups": groups},
    )
    await io.write(result)
