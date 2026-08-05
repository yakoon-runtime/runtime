from y5n.sdk import ports, runtime, session


async def main():
    doc = ports.get("document")
    current = await session.current()
    user = current.user or ""

    result = await doc.render(name="default", state={"user": user})
    await runtime.io.write(result)
