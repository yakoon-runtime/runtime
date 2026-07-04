from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, WorldService


async def run(space: NodeSpace):
    world_name = space.request.option("world")
    parent_id = space.request.option("parent")
    name = space.request.arg(0) or space.request.option("name") or ""
    description = space.request.option("description") or ""

    if not world_name:
        yield out_text("Error: --world is required.")
        return

    worlds = space.ports.get(WorldService)
    world = await worlds.get_world_by_name(world_name)
    if world is None:
        yield out_text(f"Not found: {world_name}")
        return

    boxes = space.ports.get(BoxService)
    try:
        box = await boxes.add_box(
            world_id=world.id,
            parent_id=parent_id,
            name=name,
            description=description,
        )
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Box #{box.id} '{box.name}' created in '{world.name}'.")
