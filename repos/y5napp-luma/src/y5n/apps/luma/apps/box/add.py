from y5n.sdk import context, io, ports


async def main():
    name = context.request().arg(0)
    world_ref = context.request().option("world")
    parent_id = context.request().option("parent")
    description = context.request().option("description") or ""

    if not world_ref:
        await io.write("Error: --world is required.")
        return

    worlds = ports.get("luma.world.service")
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(name=world_id)
        if w is None:
            await io.write(f"Not found: {world_ref}")
            return
        world_id = w.id

    boxes = ports.get("luma.box.service")
    try:
        box = await boxes.add_box(
            world_id=world_id,
            parent_id=parent_id,
            name=name,
            description=description,
        )
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Box #{box.id} '{box.name}' created.")
