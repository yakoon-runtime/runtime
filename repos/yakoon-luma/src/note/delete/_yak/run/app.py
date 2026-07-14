from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import NOTE_SERVICE


async def run(space: NodeSpace):
    name = space.request.arg(0)
    if not name:
        yield out_text("Error: note name is required.")
        return

    notes = space.ports.get(NOTE_SERVICE)
    note = await notes.find_note_by_name(name)
    if note is None:
        yield out_text(f"Note '{name}' not found.")
        return

    try:
        await notes.delete_note(note.id)
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Note '{name}' deleted.")
