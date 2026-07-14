from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import BOX_SERVICE, WORLD_SERVICE


async def run(space: NodeSpace):
    name_ref = space.request.arg(0)
    world_ref = space.request.option("world")

    if not name_ref:
        yield out_text("Error: box name is required.")
        return
    if not world_ref:
        yield out_text("Error: --world is required.")
        return

    worlds = space.ports.get(WORLD_SERVICE)
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(world_id)
        if w is None:
            yield out_text("World not found.")
            return
        world_id = w.id

    boxes = space.ports.get(BOX_SERVICE)
    box = await boxes.find_box(world_id=world_id, name=name_ref)
    if box is None:
        yield out_text(f"Box '{name_ref}' not found.")
        return

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
