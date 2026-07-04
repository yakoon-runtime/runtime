from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, WorldService


async def run(space: NodeSpace):
    box_id = space.request.arg(0)

    if not box_id:
        yield out_text("Error: box id is required.")
        return

    boxes = space.ports.get(BoxService)
    box = await boxes.get_box(box_id)
    if box is None:
        yield out_text(f"Not found: #{box_id}")
        return

    worlds = space.ports.get(WorldService)
    world = await worlds.get_world(box.world_id)

    lines = [
        f"Box #{box.id}",
        f"  Name: {box.name}",
    ]
    if world:
        lines.append(f"  World: {world.name} (#{world.id})")
    else:
        lines.append(f"  World: #{box.world_id}")
    if box.parent_id:
        lines.append(f"  Parent: #{box.parent_id}")
    if box.description:
        lines.append(f"  Description: {box.description}")
    yield out_text("\n".join(lines))
