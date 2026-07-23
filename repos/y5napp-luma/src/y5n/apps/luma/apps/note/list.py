from y5n.sdk import context, io, ports, session


async def main():
    box_ref = context.request().option("box")
    world_ref = context.request().option("world")

    notes = ports.get("luma.note.service")

    if box_ref:
        if not world_ref:
            await io.write("Error: --world required with --box.")
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
        box = (
            await boxes.find_box(world_id=world_id, name=box_ref)
            if not box_ref.isdigit()
            else await boxes.get_box(box_ref)
        )
        if box is None:
            await io.write("Box not found.")
            return
        linked = await notes.notes_for_box(box.id)
        if not linked:
            await io.write(f"No notes on '{box.name}'.")
            return
        lines = [f"Notes on '{box.name}':"]
        for n in linked:
            lines.append(f"  {n.name}")
        await io.write("\n".join(lines))
        return

    all_notes = await notes.list_notes()
    if not all_notes:
        await io.write("No notes.")
        return
    lines = ["Notes:"]
    for n in all_notes:
        lines.append(f"  #{n.id} {n.name}")
    await io.write("\n".join(lines))
