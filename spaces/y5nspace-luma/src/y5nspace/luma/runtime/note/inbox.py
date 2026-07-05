from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import NoteService


async def run(space: NodeSpace):
    notes = space.ports.get(NoteService)
    unplaced = await notes.inbox()

    if not unplaced:
        yield out_text("Inbox empty.")
        return

    lines = ["Inbox:"]
    for n in unplaced:
        lines.append(f"  #{n.id} {n.name}")
    yield out_text("\n".join(lines))
