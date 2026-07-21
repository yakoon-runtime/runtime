from y5n.sdk import io, ports


async def main():
    users_svc = ports.get("ident.users")
    ns_svc = ports.get("ident.namespaces")
    namespace = ns_svc.user_namespace()
    users = await users_svc.list_users(namespace=namespace)

    doc = ports.get("document")
    result = await doc.render(
        name="default",
        state={"users": users},
    )
    await io.write(result)
