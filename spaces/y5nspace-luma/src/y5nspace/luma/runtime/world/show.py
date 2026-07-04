from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import WorldService


async def run(space: NodeSpace):
    name = space.request.arg(0)

    worlds = space.ports.get(WorldService)
    world = await worlds.get_world(name)
    if world is None:
        yield out_text(f"Not found: {name}")
        return

    yield out_text(f"World: {world.name}\n  {world.description}")
