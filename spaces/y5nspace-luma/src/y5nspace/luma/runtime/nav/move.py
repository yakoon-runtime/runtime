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
    target_ref = space.request.option("box")

    if not name:
        yield out_text("Move what?")
        return
    if not target_ref:
        yield out_text("Move where? Use --box.")
        return

    boxes = space.ports.get(BoxService)
    items = await boxes.list_boxes(world_id=current_world, parent_id=current_box)
    item = next((b for b in items if b.name.lower() == name.lower()), None)
    if item is None:
        yield out_text(f"Nothing named '{name}' here.")
        return
    if not item.portable:
        yield out_text(f"'{name}' is not portable.")
        return

    target = next((b for b in items if b.name.lower() == target_ref.lower()), None)
    if target is None:
        yield out_text(f"Box '{target_ref}' not found here.")
        return

    await boxes.move_box(item.id, target.id)
    yield out_text(f"Moved '{name}' into '{target.name}'.")
