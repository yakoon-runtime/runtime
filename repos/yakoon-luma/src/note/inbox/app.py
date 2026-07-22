from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import NOTE_SERVICE


async def run(space: NodeSpace):
    notes = space.ports.get(NOTE_SERVICE)
    unplaced = await notes.inbox()

    if not unplaced:
        yield out_text("Inbox empty.")
        return

    lines = ["Inbox:"]
    for n in unplaced:
        lines.append(f"  #{n.id} {n.name}")
    yield out_text("\n".join(lines))
