from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, WorldService


async def run(space: NodeSpace):
    current_world = space.session.get_data("luma.current_world")
    box_name = space.request.arg(0)

    if not current_world:
        yield out_text("You are not inside any world.")
        return
    if not box_name:
        yield out_text("Inspect what?")
        return

    boxes = space.ports.get(BoxService)
    box = await boxes.find_box(world_id=current_world, name=box_name)
    if box is None:
        yield out_text(f"Nothing named '{box_name}' here.")
        return

    worlds = space.ports.get(WorldService)

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
                parts.append(f" — {b.description}")
            lines.append("".join(parts))

    yield out_text("\n".join(lines))
