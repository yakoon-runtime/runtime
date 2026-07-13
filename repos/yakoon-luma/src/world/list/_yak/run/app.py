from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import WORLD_SERVICE


async def run(space: NodeSpace):
    worlds = space.ports.get(WORLD_SERVICE)
    all_worlds = await worlds.list_worlds()

    if not all_worlds:
        yield out_text("No worlds yet.")
        return

    lines = ["Worlds:"]
    for w in all_worlds:
        entry = f"  #{w.id} {w.name}"
        if w.description:
            entry += f" — {w.description}"
        lines.append(entry)
    yield out_text("\n".join(lines))
