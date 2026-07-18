from y5n.sdk import context, ports


async def main():
    doc = ports.get("document")
    name = context.request().arg(0) or ""

    result = await doc.render(
        name="default",
        state={"name": name},
    )
    print(result)
