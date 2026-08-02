from y5n.sdk import context, io, ports


async def main():
    user = context.session().user or ""

    auth = ports.get("ident.auth")
    await auth.logout()

    doc = ports.get("document")
    projection = await doc.render(name="default", state={"user": user})
    await io.write(projection)
