from y5n.sdk import context, ports, runtime


async def main():
    doc = ports.get("document")
    name = context.request().arg(0) or ""

    result = await doc.render(
        name="default",
        state={"name": name},
    )
    await runtime.write(result)
