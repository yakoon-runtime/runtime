from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService


async def run(space: NodeSpace):
    current_box = space.session.get_data("luma.current_box")
    current_world = space.session.get_data("luma.current_world")
    if not current_box or not current_world:
        yield out_text("You are not inside any box.")
        return

    name = space.request.arg(0)
    description = space.request.option("description") or ""
    parent_ref = space.request.option("box")

    if not name:
        yield out_text("Place what?")
        return

    parent_id = current_box
    if parent_ref:
        boxes = space.ports.get(BoxService)
        items = await boxes.list_boxes(world_id=current_world, parent_id=current_box)
        target = next((b for b in items if b.name.lower() == parent_ref.lower()), None)
        if target is None:
            yield out_text(f"Box '{parent_ref}' not found here.")
            return
        parent_id = target.id

    boxes = space.ports.get(BoxService)
    try:
        box = await boxes.add_box(
            world_id=current_world,
            parent_id=parent_id,
            name=name,
            description=description,
            portable=True,
        )
    except ValueError as e:
        yield out_text(f"Error: {e}")
        return

    yield out_text(f"Placed '{box.name}'.")
