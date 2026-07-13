from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import BOX_SERVICE


async def run(space: NodeSpace):
    current_box = space.session.get_data("luma.current_box")
    current_world = space.session.get_data("luma.current_world")
    if not current_box or not current_world:
        yield out_text("You are not inside any box.")
        return

    name = space.request.arg(0)
    if not name:
        yield out_text("Drop what?")
        return

    inv_id = space.session.get_data("luma.inventory_id")
    if not inv_id:
        yield out_text("Nothing in inventory.")
        return

    boxes = space.ports.get(BOX_SERVICE)
    items = await boxes.list_boxes(world_id=current_world, parent_id=inv_id)
    item = next((b for b in items if b.name.lower() == name.lower()), None)
    if item is None:
        yield out_text(f"Nothing named '{name}' in inventory.")
        return

    await boxes.move_box(item.id, current_box)
    yield out_text(f"Dropped '{name}'.")
