from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import WORLD_SERVICE


async def run(space: NodeSpace):
    name = space.request.arg(0)

    worlds = space.ports.get(WORLD_SERVICE)
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
