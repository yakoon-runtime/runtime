from y5n.sdk import io, network


async def main():
    runtimes = await network.list()

    if not runtimes:
        await io.write("No known remote runtimes.")
        return

    lines = [f"  {r['name']:<20} {r['url']}" for r in runtimes]
    await io.write("Known remote runtimes:\n" + "\n".join(lines))
