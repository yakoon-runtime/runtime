from y5n.sdk import context, io, ports, session


async def main():
    current_world = session.get("luma.current_world")
    box_name = context.request().arg(0)

    if not current_world:
        await io.write("You are not inside any world.")
        return
    if not box_name:
        await io.write("Inspect what?")
        return

    boxes = ports.get("luma.box.service")
    box = await boxes.find_box(world_id=current_world, name=box_name)
    if box is None:
        await io.write(f"Nothing named '{box_name}' here.")
        return

    lines = [f"[{box.name}]"]
    if box.description:
        lines.append(f"  {box.description}")

    items = await boxes.list_boxes(world_id=current_world, parent_id=box.id)
    items = [b for b in items if b.portable]
    if items:
        lines.append("")
        lines.append("Contains:")
        for b in items:
            parts = [f"  {b.name}"]
            if b.description:
                parts.append(f" - {b.description}")
            lines.append("".join(parts))

    notes = ports.get("luma.note.service")
    linked = await notes.notes_for_box(box.id)
    if linked:
        lines.append("")
        lines.append("Notes:")
        for n in linked:
            lines.append(f"  {n.name}")

    await io.write("\n".join(lines))
