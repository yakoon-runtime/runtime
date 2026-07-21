from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    username = req.arg(0)
    changes = {
        "password": req.option("password"),
        "enabled": req.option("enabled"),
    }

    ns_svc = ports.get("ident.namespaces")
    namespace = await ns_svc.user_namespace()

    users_svc = ports.get("ident.users")
    user = await users_svc.edit_user(
        namespace=namespace,
        username=username,
        changes=changes,
    )

    doc = ports.get("document")
    result = await doc.render(
        name="default",
        state={"user": user},
    )
    await io.write(result)
