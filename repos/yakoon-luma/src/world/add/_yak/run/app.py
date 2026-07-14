from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import WORLD_SERVICE


async def run(space: NodeSpace):
    name = space.request.arg(0)
    description = space.request.option("description") or ""

    worlds = space.ports.get(WORLD_SERVICE)
    try:
        world = await worlds.add_world(name=name, description=description)
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"World #{world.id} '{world.name}' created.")
