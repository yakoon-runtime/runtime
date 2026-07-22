from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import BOX_SERVICE, NOTE_SERVICE, WORLD_SERVICE


async def run(space: NodeSpace):
    current_world = space.session.get_data("luma.current_world")
    box_name = space.request.arg(0)

    if not current_world:
        yield out_text("You are not inside any world.")
        return
    if not box_name:
        yield out_text("Inspect what?")
        return

    boxes = space.ports.get(BOX_SERVICE)
    box = await boxes.find_box(world_id=current_world, name=box_name)
    if box is None:
        yield out_text(f"Nothing named '{box_name}' here.")
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

    notes = space.ports.get(NOTE_SERVICE)
    linked = await notes.notes_for_box(box.id)
    if linked:
        lines.append("")
        lines.append("Notes:")
        for n in linked:
            lines.append(f"  {n.name}")

    yield out_text("\n".join(lines))
