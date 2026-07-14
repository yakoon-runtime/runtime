from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import BOX_SERVICE, NOTE_SERVICE, WORLD_SERVICE


async def run(space: NodeSpace):
    name = space.request.arg(0)
    box_ref = space.request.option("box")
    world_ref = space.request.option("world")

    if not name:
        yield out_text("Note name is required.")
        return

    notes = space.ports.get(NOTE_SERVICE)
    note = await notes.find_note_by_name(name)
    if note is None:
        yield out_text(f"Note '{name}' not found.")
        return

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
        box = await boxes.find_box(world_id=world_id, name=box_ref)
        if box is None:
            yield out_text(f"Box '{box_ref}' not found.")
            return
        box_id = box.id
    else:
        current_box = space.session.get_data("luma.current_box")
        if not current_box:
            yield out_text("No context. Use --box or enter a box first.")
            return
        box_id = current_box

    try:
        await notes.link(note_id=note.id, box_id=box_id)
    except ValueError:
        yield out_text(f"Note '{name}' already linked here.")
        return

    yield out_text(f"Note '{name}' placed.")
