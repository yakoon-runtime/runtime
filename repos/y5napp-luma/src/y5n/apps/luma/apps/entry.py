from y5n.sdk import context, io, ports, session


async def _resolve_box(world_id: str, box_ref: str) -> str | None:
    boxes = ports.get("luma.box.service")
    if box_ref.isdigit():
        return box_ref
    all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=None)
    for b in all_boxes:
        if b.name.lower() == box_ref.lower():
            return b.id
    return None


async def main():
    world_name = context.request().arg(0)
    box_ref = context.request().option("box")

    if not world_name:
        await io.write("Error: world name is required.")
        return

    worlds = ports.get("luma.world.service")
    world = await worlds.get_world_by_name(name=world_name)
    if world is None:
        await io.write(f"Not found: {world_name}")
        return

    if not box_ref:
        await io.write(f"Entry: #{world.entry_box_id or 'not set'}")
        return

    box_id = await _resolve_box(world.id, box_ref)
    if box_id is None:
        await io.write(f"Box '{box_ref}' not found in '{world_name}'.")
        return

    try:
        await worlds.set_entry(world_id=world.id, box_id=box_id)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Entry for '{world_name}' set to box #{box_id}.")
