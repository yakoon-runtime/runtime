from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import BOX_SERVICE, WORLD_SERVICE


async def run(space: NodeSpace):
    world_ref = space.request.option("world")
    parent_id = space.request.option("parent")
    name = space.request.arg(0)
    description = space.request.option("description") or ""

    if not world_ref:
        yield out_text("Error: --world is required.")
        return

    worlds = space.ports.get(WORLD_SERVICE)
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(world_id)
        if w is None:
            yield out_text(f"Not found: {world_ref}")
            return
        world_id = w.id

    boxes = space.ports.get(BOX_SERVICE)
    try:
        box = await boxes.add_box(
            world_id=world_id,
            parent_id=parent_id,
            name=name,
            description=description,
        )
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Box #{box.id} '{box.name}' created.")
