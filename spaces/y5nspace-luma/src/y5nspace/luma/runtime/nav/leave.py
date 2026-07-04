from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace


async def run(space: NodeSpace):
    current_world = space.session.data.get("luma.current_world")
    current_box = space.session.data.get("luma.current_box")

    if current_world is None and current_box is None:
        yield out_text("Nowhere to leave.")
        return

    space.session.data.pop("luma.current_world", None)
    space.session.data.pop("luma.current_box", None)

    parts = []
    if current_world:
        parts.append(f"'{current_world}'")
    if current_box:
        parts.append(f"box #{current_box}")
    yield out_text(f"Left {' '.join(parts)}.")
