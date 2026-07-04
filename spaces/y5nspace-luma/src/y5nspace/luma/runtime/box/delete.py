from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, WorldService


async def run(space: NodeSpace):
    name_ref = space.request.arg(0)
    world_ref = space.request.option("world")

    if not name_ref:
        yield out_text("Error: box name is required.")
        return
    if not world_ref:
        yield out_text("Error: --world is required.")
        return

    worlds = space.ports.get(WorldService)
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(world_id)
        if w is None:
            yield out_text("World not found.")
            return
        world_id = w.id

    boxes = space.ports.get(BoxService)
    all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=None)
    box = next((b for b in all_boxes if b.name.lower() == name_ref.lower()), None)
    if box is None:
        yield out_text(f"Box '{name_ref}' not found.")
        return

    try:
        await boxes.delete_box(box.id)
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Box '{name_ref}' deleted.")
