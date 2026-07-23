from y5n.sdk import context, io, ports, session


async def main():
    name_ref = context.request().arg(0)
    world_ref = context.request().option("world")
    new_name = context.request().option("new-name")
    description = context.request().option("description")

    if not name_ref:
        await io.write("Error: box name is required.")
        return
    if not world_ref:
        await io.write("Error: --world is required.")
        return

    worlds = ports.get("luma.world.service")
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(world_id)
        if w is None:
            await io.write("World not found.")
            return
        world_id = w.id

    boxes = ports.get("luma.box.service")
    box = await boxes.find_box(world_id=world_id, name=name_ref)
    if box is None:
        await io.write(f"Box '{name_ref}' not found.")
        return

    try:
        await boxes.update_box(
            box_id=box.id,
            name=new_name or box.name,
            description=description or box.description,
        )
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Box '{name_ref}' updated.")
