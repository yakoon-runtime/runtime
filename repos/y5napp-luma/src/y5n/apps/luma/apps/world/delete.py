from y5n.sdk import context, io, ports, session


async def main():
    name = context.request().arg(0)

    worlds = ports.get("luma.world.service")
    world = await worlds.get_world_by_name(name)
    if world is None:
        await io.write(f"Not found: {name}")
        return

    try:
        await worlds.delete_world(world.id)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"World '{name}' deleted.")
