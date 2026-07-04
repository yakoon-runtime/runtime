from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import WorldService


async def run(space: NodeSpace):
    name = space.request.arg(0)

    worlds = space.ports.get(WorldService)
    try:
        await worlds.delete_world(name)
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"World '{name}' deleted.")
