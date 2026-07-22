from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import BOX_SERVICE


async def run(space: NodeSpace):
    current_world = space.session.get_data("luma.current_world")
    inv_id = space.session.get_data("luma.inventory_id")

    if not inv_id or not current_world:
        yield out_text("Nothing in inventory.")
        return

    boxes = space.ports.get(BOX_SERVICE)
    items = await boxes.list_boxes(world_id=current_world, parent_id=inv_id)

    if not items:
        yield out_text("Nothing in inventory.")
        return

    lines = ["Inventory:"]
    for b in items:
        parts = [f"  {b.name}"]
        if b.description:
            parts.append(f" - {b.description}")
        lines.append("".join(parts))
    yield out_text("\n".join(lines))
