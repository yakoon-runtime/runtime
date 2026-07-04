from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import WorldService


async def run(space: NodeSpace):
    worlds = space.ports.get(WorldService)
    all_worlds = await worlds.list_worlds()

    if not all_worlds:
        yield out_text("No worlds yet.")
        return

    lines = ["Worlds:"]
    for w in all_worlds:
        lines.append(f"  {w.name} — {w.description or '(no description)'}")
    yield out_text("\n".join(lines))
