from y5n.sdk import context, ports, runtime


async def main():
    doc = ports.get("document")
    user = context.session().user or ""

    result = await doc.render(name="default", state={"user": user})
    await runtime.io.write(result)
