from y5n.sdk import context, io, ports


async def main():
    current_box = context.session().data.get("luma.current_box")
    current_world = context.session().data.get("luma.current_world")

    if not current_box:
        await io.write("You are not inside any box. Use 'enter' first.")
        return

    boxes = ports.get("luma.box.service")
    box = await boxes.get_box(box_id=current_box)
    if box is None:
        await io.write("Current box not found.")
        return

    worlds = ports.get("luma.world.service")
    world = await worlds.get_world(world_id=current_world)

    lines = [f"[{box.name}]"]
    if box.description:
        lines.append(f"  {box.description}")

    exits = ports.get("luma.exit.service")
    from_here = await exits.find_from(box_id=box.id)

    if from_here:
        lines.append("")
        lines.append("Exits:")
        for e in from_here:
            target = await boxes.get_box(box_id=e.target_box_id)
            target_name = target.name if target else f"#{e.target_box_id}"
            label = e.name or e.direction or "?"
            if e.direction and e.name:
                lines.append(f"  {e.direction}: {label} -> {target_name}")
            else:
                lines.append(f"  {label} -> {target_name}")

    items = await boxes.list_boxes(world_id=current_world, parent_id=current_box)
    items = [b for b in items if b.portable]
    if items:
        lines.append("")
        lines.append("Contains:")
        for b in items:
            parts = [f"  {b.name}"]
            if b.description:
                parts.append(f" - {b.description}")
            lines.append("".join(parts))

    await io.write("\n".join(lines))
