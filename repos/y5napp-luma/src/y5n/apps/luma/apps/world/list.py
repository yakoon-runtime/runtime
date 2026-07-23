from y5n.sdk import context, io, ports, session


async def main():
    worlds = ports.get("luma.world.service")
    all_worlds = await worlds.list_worlds()

    if not all_worlds:
        await io.write("No worlds yet.")
        return

    lines = ["Worlds:"]
    for w in all_worlds:
        entry = f"  #{w.id} {w.name}"
        if w.description:
            entry += f" — {w.description}"
        lines.append(entry)
    await io.write("\n".join(lines))
