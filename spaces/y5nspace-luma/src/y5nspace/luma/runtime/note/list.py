from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, NoteService, WorldService


async def _resolve_world(space, world_ref: str | None) -> str | None:
    if world_ref is None:
        return None
    if world_ref.isdigit():
        return world_ref
    worlds = space.ports.get(WorldService)
    w = await worlds.get_world_by_name(world_ref)
    return w.id if w else None


async def run(space: NodeSpace):
    box_ref = space.request.option("box") or space.session.get_data("luma.current_box")
    world_ref = space.request.option("world") or space.session.get_data("luma.current_world")

    notes = space.ports.get(NoteService)

    if box_ref:
        world_id = await _resolve_world(space, world_ref)
        if world_id is None:
            yield out_text("Error: --world or context required.")
            return
        boxes = space.ports.get(BoxService)
        box = await boxes.find_box(world_id=world_id, name=box_ref) if not box_ref.isdigit() else await boxes.get_box(box_ref)
        if box is None:
            yield out_text(f"Box not found.")
            return
        linked = await notes.notes_for_box(box.id)
        if not linked:
            yield out_text(f"No notes on '{box.name}'.")
            return
        lines = [f"Notes on '{box.name}':"]
        for n in linked:
            lines.append(f"  {n.name}")
        yield out_text("\n".join(lines))
        return

    all_notes = await notes.list_notes()
    if not all_notes:
        yield out_text("No notes.")
        return
    lines = ["Notes:"]
    for n in all_notes:
        lines.append(f"  #{n.id} {n.name}")
    yield out_text("\n".join(lines))
