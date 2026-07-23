from y5n.sdk import context, io, ports, session


async def main():
    name = context.request().arg(0)
    new_name = context.request().option("new-name")
    description = context.request().option("description")
    entry_box_id = context.request().option("entry")

    worlds = ports.get("luma.world.service")
    world = await worlds.get_world_by_name(name)
    if world is None:
        await io.write(f"Not found: {name}")
        return

    try:
        await worlds.update_world(
            world_id=world.id,
            name=new_name or name,
            description=description,
            entry_box_id=entry_box_id,
        )
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    display_name = new_name or name
    await io.write(f"World '{display_name}' updated.")
