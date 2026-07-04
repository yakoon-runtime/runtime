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

    try:
        await worlds.delete_world(world.id)
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"World '{name}' deleted.")
