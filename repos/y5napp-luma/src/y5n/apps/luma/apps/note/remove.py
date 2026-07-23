from y5n.sdk import context, io, ports, session


async def _resolve_box_id(space, box_ref: str, world_ref: str | None) -> str | None:
    if box_ref == "." or box_ref is None:
        return session.get("luma.current_box")
    if box_ref.isdigit():
        return box_ref
    if not world_ref:
        return None
    worlds = ports.get("luma.world.service")
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(name=world_id)
        if w is None:
            return None
        world_id = w.id
    boxes = ports.get("luma.box.service")
    box = await boxes.find_box(world_id=world_id, name=box_ref)
    return box.id if box else None


async def main():
    name = context.request().arg(0)
    box_ref = context.request().option("box")
    world_ref = context.request().option("world")

    if not name:
        await io.write("Note name is required.")
        return

    notes = ports.get("luma.note.service")
    note = await notes.find_note_by_name(name=name)
    if note is None:
        await io.write(f"Note '{name}' not found.")
        return

    box_id = await _resolve_box_id(space, box_ref, world_ref)
    if box_id is None:
        await io.write("Box not found.")
        return

    try:
        await notes.unlink(note_id=note.id, box_id=box_id)
    except ValueError:
        await io.write(f"Note '{name}' is not linked here.")
        return

    await io.write(f"Note '{name}' removed.")
