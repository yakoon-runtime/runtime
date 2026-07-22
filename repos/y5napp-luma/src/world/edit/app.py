from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import WORLD_SERVICE


async def run(space: NodeSpace):
    name = space.request.arg(0)
    new_name = space.request.option("new-name")
    description = space.request.option("description")
    entry_box_id = space.request.option("entry")

    worlds = space.ports.get(WORLD_SERVICE)
    world = await worlds.get_world_by_name(name)
    if world is None:
        yield out_text(f"Not found: {name}")
        return

    try:
        await worlds.update_world(
            world_id=world.id,
            name=new_name or name,
            description=description,
            entry_box_id=entry_box_id,
        )
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    display_name = new_name or name
    yield out_text(f"World '{display_name}' updated.")
