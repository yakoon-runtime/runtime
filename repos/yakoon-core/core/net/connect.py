from y5n.sdk import context, io, network, viewport


async def main():
    name = context.request().arg(0)
    url = await network.resolve(name)

    if not url:
        await io.write(f"Unknown runtime: {name}")
        return

    await viewport.connect(url=url, name=name)
