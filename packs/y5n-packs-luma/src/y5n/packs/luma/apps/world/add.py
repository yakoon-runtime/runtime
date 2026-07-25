from y5n.sdk import context, io, ports


async def main():
    name = context.request().arg(0)
    description = context.request().option("description") or ""

    worlds = ports.get("luma.world.service")
    try:
        world = await worlds.add_world(name=name, description=description)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"World #{world.id} '{world.name}' created.")
