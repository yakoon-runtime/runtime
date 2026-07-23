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
        await io.write("Enter where?")
        return

    worlds = ports.get("luma.world.service")
    world = await worlds.get_world_by_name(name=world_name)
    if world is None:
        await io.write(f"Not found: {world_name}")
        return

    target = world.entry_box_id
    if box_ref:
        resolved = await _resolve_box(world.id, box_ref)
        if resolved is None:
            await io.write(f"Box '{box_ref}' not found in '{world_name}'.")
            return
        target = resolved

    if target is None:
        await io.write(f"World '{world_name}' has no entry set.")
        return

    boxes = ports.get("luma.box.service")
    box = await boxes.get_box(box_id=target)
    if box is None:
        await io.write(f"Entry box #{target} not found.")
        return

    session.set("luma.current_world", world.id)
    session.set("luma.current_box", box.id)

    await io.write(f"Entered '{world.name}' at '{box.name}'.")
