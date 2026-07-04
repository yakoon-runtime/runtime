from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import WorldService


async def run(space: NodeSpace):
    name = space.request.arg(0)
    description = space.request.option("description") or ""

    worlds = space.ports.get(WorldService)
    try:
        world = await worlds.add_world(name=name, description=description)
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"World #{world.id} '{world.name}' created.")
