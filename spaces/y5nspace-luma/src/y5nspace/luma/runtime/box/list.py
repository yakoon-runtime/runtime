from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, WorldService


async def run(space: NodeSpace):
    world_ref = space.request.option("world")
    parent_id = space.request.option("parent")

    world_id = world_ref
    if world_id and not world_id.isdigit():
        worlds = space.ports.get(WorldService)
        w = await worlds.get_world_by_name(world_id)
        if w is None:
            yield out_text(f"World not found.")
            return
        world_id = w.id

    boxes = space.ports.get(BoxService)
    all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=parent_id)

    if not all_boxes:
        yield out_text("No boxes here.")
        return

    lines = ["Boxes:"]
    for b in all_boxes:
        desc = f" — {b.description}" if b.description else ""
        lines.append(f"  #{b.id} {b.name}{desc}")
    yield out_text("\n".join(lines))
