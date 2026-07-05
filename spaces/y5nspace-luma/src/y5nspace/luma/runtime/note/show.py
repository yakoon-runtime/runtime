from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import NoteService


async def run(space: NodeSpace):
    name = space.request.arg(0)

    if not name:
        yield out_text("Show which note?")
        return

    notes = space.ports.get(NoteService)
    note = await notes.find_note_by_name(name)
    if note is None:
        yield out_text(f"Note '{name}' not found.")
        return

    yield out_text(f"{note.name}\n\n{note.content}")
