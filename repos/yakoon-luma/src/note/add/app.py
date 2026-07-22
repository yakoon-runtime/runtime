from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import NOTE_SERVICE


async def run(space: NodeSpace):
    name = space.request.arg(0)
    content = space.request.option("content") or ""

    if not name:
        yield out_text("Error: note name is required.")
        return

    notes = space.ports.get(NOTE_SERVICE)
    try:
        note = await notes.add_note(name=name, content=content)
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Note '{note.name}' created.")
