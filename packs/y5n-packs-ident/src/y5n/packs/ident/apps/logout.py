from y5n.sdk import io, ports, session


async def main():
    current = await session.current()
    user = current.user or ""

    auth = ports.get("ident.auth")
    await auth.logout()

    doc = ports.get("document")
    projection = await doc.render(name="default", state={"user": user})
    await io.write(projection)
