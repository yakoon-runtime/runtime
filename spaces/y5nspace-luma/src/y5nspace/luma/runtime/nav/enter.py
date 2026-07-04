from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, WorldService


async def _resolve_box(space, world_id: str, box_ref: str) -> str | None:
    boxes = space.ports.get(BoxService)
    if box_ref.isdigit():
        return box_ref
    all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=None)
    for b in all_boxes:
        if b.name.lower() == box_ref.lower():
            return b.id
    return None


async def run(space: NodeSpace):
    world_name = space.request.arg(0)
    box_ref = space.request.option("box")

    if not world_name:
        yield out_text("Enter where?")
        return

    worlds = space.ports.get(WorldService)
    world = await worlds.get_world_by_name(world_name)
    if world is None:
        yield out_text(f"Not found: {world_name}")
        return

    target = world.entry_box_id
    if box_ref:
        resolved = await _resolve_box(space, world.id, box_ref)
        if resolved is None:
            yield out_text(f"Box '{box_ref}' not found in '{world_name}'.")
            return
        target = resolved

    if target is None:
        yield out_text(f"World '{world_name}' has no entry set.")
        return

    boxes = space.ports.get(BoxService)
    box = await boxes.get_box(target)
    if box is None:
        yield out_text(f"Entry box #{target} not found.")
        return

    space.session.data.set("luma.current_world", world.id)
    space.session.data.set("luma.current_box", box.id)

    yield out_text(f"Entered '{world.name}' at '{box.name}'.")
