from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, NoteService, WorldService


async def _resolve_box(space, box_ref: str, current_world: str | None) -> str | None:
    if box_ref == "." or box_ref is None:
        return space.session.get_data("luma.current_box")
    if box_ref.isdigit():
        return box_ref
    if not current_world:
        return None
    boxes = space.ports.get(BoxService)
    worlds = space.ports.get(WorldService)
    world_id = current_world
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(world_id)
        if w is None:
            return None
        world_id = w.id
    box = await boxes.find_box(world_id=world_id, name=box_ref)
    return box.id if box else None


async def run(space: NodeSpace):
    current_box = space.session.get_data("luma.current_box")
    current_world = space.session.get_data("luma.current_world")
    name = space.request.arg(0)
    box_ref = space.request.option("box") or current_box

    if not name:
        yield out_text("Note name is required.")
        return
    if not box_ref:
        yield out_text("No context.")
        return

    notes = space.ports.get(NoteService)
    note = await notes.find_note_by_name(name)
    if note is None:
        yield out_text(f"Note '{name}' not found.")
        return

    box_id = await _resolve_box(space, box_ref, current_world)
    if box_id is None:
        yield out_text("Box not found.")
        return

    try:
        await notes.unlink(note.id, box_id)
    except ValueError:
        yield out_text(f"Note '{name}' is not linked here.")
        return

    yield out_text(f"Note '{name}' removed.")
