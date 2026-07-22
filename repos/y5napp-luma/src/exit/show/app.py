from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import BOX_SERVICE, EXIT_SERVICE, WORLD_SERVICE


async def run(space: NodeSpace):
    exit_name = space.request.arg(0)
    world_ref = space.request.option("world")
    box_ref = space.request.option("box")

    if not exit_name:
        yield out_text("Error: exit name is required.")
        return
    if not world_ref:
        yield out_text("Error: --world is required.")
        return
    if not box_ref:
        yield out_text("Error: --box is required.")
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
    all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=None)
    src = next((b for b in all_boxes if b.name.lower() == box_ref.lower()), None)
    if src is None:
        yield out_text(f"Box '{box_ref}' not found.")
        return

    exits = space.ports.get(EXIT_SERVICE)
    from_src = await exits.find_from(src.id)
    e = next((ex for ex in from_src if ex.name.lower() == exit_name.lower()), None)
    if e is None:
        yield out_text(f"Exit '{exit_name}' not found in '{box_ref}'.")
        return

    target = await boxes.get_box(e.target_box_id)
    tgt_name = target.name if target else f"#{e.target_box_id}"

    lines = [
        f"Exit '{e.name}'",
        f"  From: {box_ref} (#{e.source_box_id})",
        f"  To:   {tgt_name} (#{e.target_box_id})",
    ]
    if e.direction:
        lines.append(f"  Direction: {e.direction}")
    if e.description:
        lines.append(f"  Description: {e.description}")
    yield out_text("\n".join(lines))
