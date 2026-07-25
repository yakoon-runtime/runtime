from y5n.sdk import context, io, ports


async def main():
    exit_name = context.request().arg(0)
    world_ref = context.request().option("world")
    box_ref = context.request().option("box")
    new_name = context.request().option("new-name")
    description = context.request().option("description")
    direction = context.request().option("direction")

    worlds = ports.get("luma.world.service")
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(name=world_id)
        if w is None:
            await io.write("World not found.")
            return
        world_id = w.id

    boxes = ports.get("luma.box.service")
    all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=None)
    src = next((b for b in all_boxes if b.name.lower() == box_ref.lower()), None)
    if src is None:
        await io.write(f"Box '{box_ref}' not found.")
        return

    exits = ports.get("luma.exit.service")
    from_src = await exits.find_from(box_id=src.id)
    e = next((ex for ex in from_src if ex.name.lower() == exit_name.lower()), None)
    if e is None:
        await io.write(f"Exit '{exit_name}' not found in '{box_ref}'.")
        return

    final_name = new_name if new_name is not None else e.name
    final_desc = description if description is not None else e.description
    final_dir = direction if direction is not None else e.direction

    await exits.disconnect(exit_id=e.id)
    await exits.connect(
        world_id=e.world_id,
        source_box_id=e.source_box_id,
        target_box_id=e.target_box_id,
        name=final_name,
        description=final_desc,
        direction=final_dir,
    )
    await io.write(f"Exit '{exit_name}' updated.")
