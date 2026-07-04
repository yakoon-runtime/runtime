from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService


async def run(space: NodeSpace):
    box_id = space.request.arg(0)
    name = space.request.option("name")
    description = space.request.option("description")

    if not box_id:
        yield out_text("Error: box id is required.")
        return

    boxes = space.ports.get(BoxService)
    try:
        await boxes.update_box(
            box_id=box_id,
            name=name or "",
            description=description or "",
        )
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Box #{box_id} updated.")
