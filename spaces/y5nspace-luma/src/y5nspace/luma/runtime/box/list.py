from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, WorldService


async def _resolve_world(space, world_ref: str | None) -> str | None:
    if world_ref is None:
        return space.session.data.get("luma.current_world")
    if world_ref.isdigit():
        return world_ref
    worlds = space.ports.get(WorldService)
    w = await worlds.get_world_by_name(world_ref)
    return w.id if w else None


async def run(space: NodeSpace):
    world_ref = space.request.option("world") or space.session.data.get("luma.current_world")
    parent_id = space.request.option("parent") or space.session.data.get("luma.current_box")

    if not world_ref:
        yield out_text("Error: --world is required.")
        return

    world_id = await _resolve_world(space, world_ref)
    if world_id is None:
        yield out_text(f"World not found.")
        return

    boxes = space.ports.get(BoxService)
    all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=parent_id)

    if not all_boxes:
        yield out_text("No boxes here.")
        return

    lines = [f"Boxes:"]
    for b in all_boxes:
        desc = f" — {b.description}" if b.description else ""
        lines.append(f"  #{b.id} {b.name}{desc}")
    yield out_text("\n".join(lines))
