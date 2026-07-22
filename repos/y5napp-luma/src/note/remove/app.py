from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import BOX_SERVICE, NOTE_SERVICE, WORLD_SERVICE


async def _resolve_box_id(space, box_ref: str, world_ref: str | None) -> str | None:
    if box_ref == "." or box_ref is None:
        return space.session.get_data("luma.current_box")
    if box_ref.isdigit():
        return box_ref
    if not world_ref:
        return None
    worlds = space.ports.get(WORLD_SERVICE)
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(world_id)
        if w is None:
            return None
        world_id = w.id
    boxes = space.ports.get(BOX_SERVICE)
    box = await boxes.find_box(world_id=world_id, name=box_ref)
    return box.id if box else None


async def run(space: NodeSpace):
    name = space.request.arg(0)
    box_ref = space.request.option("box")
    world_ref = space.request.option("world")

    if not name:
        yield out_text("Note name is required.")
        return

    notes = space.ports.get(NOTE_SERVICE)
    note = await notes.find_note_by_name(name)
    if note is None:
        yield out_text(f"Note '{name}' not found.")
        return

    box_id = await _resolve_box_id(space, box_ref, world_ref)
    if box_id is None:
        yield out_text("Box not found.")
        return

    try:
        await notes.unlink(note.id, box_id)
    except ValueError:
        yield out_text(f"Note '{name}' is not linked here.")
        return

    yield out_text(f"Note '{name}' removed.")
