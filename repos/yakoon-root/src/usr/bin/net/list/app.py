from y5n.sdk import ports, runtime


async def main():
    src = ports.get("source")
    result = await src.read(query="system:runtimes --list")

    if not result.rows:
        await runtime.io.write("No known remote runtimes.")
        return

    lines = [f"  {r['name']:<20} {r['url']}" for r in result.rows]
    await runtime.io.write("Known remote runtimes:\n" + "\n".join(lines))
