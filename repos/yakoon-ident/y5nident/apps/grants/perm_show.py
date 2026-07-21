from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    permission_key = req.arg(0)

    ns_svc = ports.get("ident.namespaces")
    permgrant_svc = ports.get("ident.permgrant")

    grants = await permgrant_svc.list_permission_grants(
        namespace=await ns_svc.permgrant_namespace(), permission_key=permission_key,
    )
    doc = ports.get("document")
    result = await doc.render(name="default", state={"grants": grants, "permission": permission_key})
    await io.write(result)
