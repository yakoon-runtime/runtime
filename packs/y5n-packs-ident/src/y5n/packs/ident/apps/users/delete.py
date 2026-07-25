from y5n.sdk import context, io, ports


async def main():

    req = context.request()
    username = req.arg(0)

    ns_svc = ports.get("ident.namespaces")
    namespace = await ns_svc.user_namespace()

    users_svc = ports.get("ident.users")
    await users_svc.delete_user(
        namespace=namespace,
        username=username,
    )

    doc = ports.get("document")
    result = await doc.render(
        name="default",
        state={"name": username},
    )
    await io.write(result)
