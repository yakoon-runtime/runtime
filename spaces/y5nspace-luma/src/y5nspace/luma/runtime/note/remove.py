from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import NoteService


async def run(space: NodeSpace):
    current_box = space.session.get_data("luma.current_box")
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

    try:
        await notes.unlink(note.id, box_ref)
    except ValueError:
        yield out_text(f"Note '{name}' is not linked here.")
        return

    yield out_text(f"Note '{name}' removed.")
