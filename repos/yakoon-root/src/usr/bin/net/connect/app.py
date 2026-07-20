from y5n.sdk import context, runtime


async def main():
    name = context.request().arg(0)
    url = await runtime.network.resolve(name)

    if not url:
        await runtime.io.write(f"Unknown runtime: {name}")
        return

    await runtime.view(connect=url, connect_name=name)
