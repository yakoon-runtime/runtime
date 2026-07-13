from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import BOX_SERVICE, NOTE_SERVICE, WORLD_SERVICE


async def run(space: NodeSpace):
    box_ref = space.request.option("box")
    world_ref = space.request.option("world")

    notes = space.ports.get(NOTE_SERVICE)

    if box_ref:
        if not world_ref:
            yield out_text("Error: --world required with --box.")
            return
        worlds = space.ports.get(WORLD_SERVICE)
        world_id = world_ref
        if not world_id.isdigit():
            w = await worlds.get_world_by_name(world_id)
            if w is None:
                yield out_text("World not found.")
                return
            world_id = w.id
        boxes = space.ports.get(BOX_SERVICE)
        box = await boxes.find_box(world_id=world_id, name=box_ref) if not box_ref.isdigit() else await boxes.get_box(box_ref)
        if box is None:
            yield out_text("Box not found.")
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
