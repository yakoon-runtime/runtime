from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, NoteService, WorldService


async def run(space: NodeSpace):
    current_box = space.session.get_data("luma.current_box")
    current_world = space.session.get_data("luma.current_world")
    name = space.request.arg(0)
    box_ref = space.request.option("box")

    if not name:
        yield out_text("Note name is required.")
        return

    notes = space.ports.get(NoteService)
    note = await notes.find_note_by_name(name)
    if note is None:
        yield out_text(f"Note '{name}' not found.")
        return

    if box_ref:
        if box_ref == ".":
            box_id = current_box
        else:
            if not current_world:
                yield out_text("No world context. Use --world.")
                return
            boxes = space.ports.get(BoxService)
            box = await boxes.find_box(world_id=current_world, name=box_ref)
            if box is None:
                yield out_text(f"Box '{box_ref}' not found.")
                return
            box_id = box.id
    else:
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
