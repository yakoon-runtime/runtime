from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import WorldService


async def run(space: NodeSpace):
    name = space.request.arg(0)

    worlds = space.ports.get(WorldService)
    world = await worlds.get_world_by_name(name)
    if world is None:
        yield out_text(f"Not found: {name}")
        return

    lines = [
        f"World #{world.id}",
        f"  Name: {world.name}",
    ]
    if world.description:
        lines.append(f"  Description: {world.description}")
    if world.entry_box_id:
        lines.append(f"  Entry: #{world.entry_box_id}")
    yield out_text("\n".join(lines))
