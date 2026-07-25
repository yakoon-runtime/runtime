from y5n.sdk import context, io, ports


async def main():

    req = context.request()
    username = req.arg(0)
    password = req.option("password")

    ns_svc = ports.get("ident.namespaces")
    namespace = await ns_svc.user_namespace()

    users_svc = ports.get("ident.users")
    user = await users_svc.add_user(
        namespace=namespace,
        username=username,
        password=password,
    )

    doc = ports.get("document")
    result = await doc.render(
        name="default",
        state={"user": user},
    )
    await io.write(result)
