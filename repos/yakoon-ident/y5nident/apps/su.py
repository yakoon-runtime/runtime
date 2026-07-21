from y5n.sdk import context, io, ports


async def main():
    req = context.request()
    username = req.arg(0) or req.option("user")
    secret = req.option("password")

    if not username or not secret:
        await io.write("Usage: su <user> --password=<password>")
        return

    auth = ports.get("authenticate")
    result = await auth(username=username, secret=secret)

    state = {"user": username, "reason": None}
    if result.ok and result.user:
        state["user"] = result.user.get("username", username)
    else:
        state["reason"] = result.reason

    doc = ports.get("document")
    projection = await doc.render(name="default", state=state)
    await io.write(projection)
