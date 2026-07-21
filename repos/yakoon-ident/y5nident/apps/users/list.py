from y5n.sdk import io, ports


async def main():

    ns_svc = ports.get("ident.namespaces")
    namespace = await ns_svc.user_namespace()

    users_svc = ports.get("ident.users")
    users = await users_svc.list_users(namespace=namespace)

    doc = ports.get("document")
    result = await doc.render(
        name="default",
        state={"users": users},
    )
    await io.write(result)
