from y5n.sdk import context, io, ports, session


async def main():
    name = context.request().arg(0)
    box_ref = context.request().option("box")
    world_ref = context.request().option("world")

    notes = ports.get("luma.note.service")
    note = await notes.find_note_by_name(name=name)
    if note is None:
        await io.write(f"Note '{name}' not found.")
        return

    if box_ref:
        if not world_ref:
            await io.write("Error: --world required with --box.")
            return
        worlds = ports.get("luma.world.service")
        world_id = world_ref
        if not world_id.isdigit():
            w = await worlds.get_world_by_name(name=world_id)
            if w is None:
                await io.write("World not found.")
                return
            world_id = w.id
        boxes = ports.get("luma.box.service")
        box = await boxes.find_box(world_id=world_id, name=box_ref)
        if box is None:
            await io.write(f"Box '{box_ref}' not found.")
            return
        box_id = box.id
    else:
        current_box = session.get("luma.current_box")
        if not current_box:
            await io.write("No context. Use --box or enter a box first.")
            return
        box_id = current_box

    try:
        await notes.link(note_id=note.id, box_id=box_id)
    except ValueError:
        await io.write(f"Note '{name}' already linked here.")
        return

    await io.write(f"Note '{name}' placed.")
