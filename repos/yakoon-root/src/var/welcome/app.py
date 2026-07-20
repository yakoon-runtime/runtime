from y5n.sdk import context, ports, runtime, viewport


async def main():
    doc = ports.get("document")
    name = context.request().arg(0) or ""

    result = await doc.render(
        name="default",
        state={"name": name},
    )
    await viewport.clear()
    await runtime.io.write(result)
