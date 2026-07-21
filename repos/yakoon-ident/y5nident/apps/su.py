from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    username = req.arg(0) or req.option("user")
    secret = req.option("password")

    if not username or not secret:
        await io.write("Usage: su <user> --password=<password>")
        return

    auth = ports.get("ident.auth")
    result = await auth(username=username, secret=secret)

    state = {"user": username, "reason": None}
    if result.get("ok") and result.get("user"):
        state["user"] = result["user"].get("username", username)
    else:
        state["reason"] = result.get("reason")

    doc = ports.get("document")
    projection = await doc.render(
        name="default",
        state=state,
    )
    await io.write(projection)
