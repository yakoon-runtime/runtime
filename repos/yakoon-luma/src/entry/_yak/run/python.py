from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import BOX_SERVICE, WORLD_SERVICE


async def _resolve_box(space, world_id: str, box_ref: str) -> str | None:
    boxes = space.ports.get(BOX_SERVICE)
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
        yield out_text("Error: world name is required.")
        return

    worlds = space.ports.get(WORLD_SERVICE)
    world = await worlds.get_world_by_name(world_name)
    if world is None:
        yield out_text(f"Not found: {world_name}")
        return

    if not box_ref:
        yield out_text(f"Entry: #{world.entry_box_id or 'not set'}")
        return

    box_id = await _resolve_box(space, world.id, box_ref)
    if box_id is None:
        yield out_text(f"Box '{box_ref}' not found in '{world_name}'.")
        return

    try:
        await worlds.set_entry(world_id=world.id, box_id=box_id)
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Entry for '{world_name}' set to box #{box_id}.")
