from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import BOX_SERVICE, EXIT_SERVICE, WORLD_SERVICE


async def run(space: NodeSpace):
    current_box = space.session.get_data("luma.current_box")
    current_world = space.session.get_data("luma.current_world")

    if not current_box:
        yield out_text("You are not inside any box. Use 'enter' first.")
        return

    boxes = space.ports.get(BOX_SERVICE)
    box = await boxes.get_box(current_box)
    if box is None:
        yield out_text("Current box not found.")
        return

    worlds = space.ports.get(WORLD_SERVICE)
    world = await worlds.get_world(current_world)

    lines = [f"[{box.name}]"]
    if box.description:
        lines.append(f"  {box.description}")

    exits = space.ports.get(EXIT_SERVICE)
    from_here = await exits.find_from(box.id)

    if from_here:
        lines.append("")
        lines.append("Exits:")
        for e in from_here:
            target = await boxes.get_box(e.target_box_id)
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

    yield out_text("\n".join(lines))
