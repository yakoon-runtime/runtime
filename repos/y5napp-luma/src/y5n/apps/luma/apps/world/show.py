from y5n.sdk import context, io, ports, session


async def main():
    name = context.request().arg(0)

    worlds = ports.get("luma.world.service")
    world = await worlds.get_world_by_name(name)
    if world is None:
        await io.write(f"Not found: {name}")
        return

    lines = [
        f"World #{world.id}",
        f"  Name: {world.name}",
    ]
    if world.description:
        lines.append(f"  Description: {world.description}")
    if world.entry_box_id:
        lines.append(f"  Entry: #{world.entry_box_id}")
    await io.write("\n".join(lines))
