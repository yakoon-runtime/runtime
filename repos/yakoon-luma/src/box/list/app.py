from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import BOX_SERVICE, WORLD_SERVICE


async def run(space: NodeSpace):
    world_ref = space.request.option("world")
    parent_id = space.request.option("parent")

    worlds = space.ports.get(WORLD_SERVICE)
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(world_id)
        if w is None:
            yield out_text("World not found.")
            return
        world_id = w.id

    boxes = space.ports.get(BOX_SERVICE)
    all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=parent_id)

    if not all_boxes:
        yield out_text("No boxes here.")
        return

    lines = ["Boxes:"]
    for b in all_boxes:
        desc = f" -- {b.description}" if b.description else ""
        lines.append(f"  #{b.id} {b.name}{desc}")
    yield out_text("\n".join(lines))
