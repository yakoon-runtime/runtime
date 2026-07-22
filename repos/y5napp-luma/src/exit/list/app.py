from __future__ import annotations

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace

from .ports import BOX_SERVICE, EXIT_SERVICE, WORLD_SERVICE


async def run(space: NodeSpace):
    world_ref = space.request.option("world")
    box_ref = space.request.option("box")

    if not world_ref:
        yield out_text("Error: --world is required.")
        return

    worlds = space.ports.get(WORLD_SERVICE)
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(world_id)
        if w is None:
            yield out_text("World not found.")
            return
        world_id = w.id

    exits = space.ports.get(EXIT_SERVICE)
    boxes = space.ports.get(BOX_SERVICE)

    if box_ref:
        all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=None)
        box_id = next(
            (b.id for b in all_boxes if b.name.lower() == box_ref.lower()), None
        )
        if box_id is None:
            yield out_text(f"Box '{box_ref}' not found.")
            return
        exits_list = await exits.find_from(box_id)
    else:
        exits_list = await exits.list_exits(world_id=world_id)

    if not exits_list:
        yield out_text("No exits.")
        return

    lines = ["Exits:"]
    for e in exits_list:
        source = await boxes.get_box(e.source_box_id)
        target = await boxes.get_box(e.target_box_id)
        src_name = source.name if source else f"#{e.source_box_id}"
        tgt_name = target.name if target else f"#{e.target_box_id}"
        line = f"  #{e.id} {e.name or '?'}: {src_name} -> {tgt_name}"
        if e.direction:
            line += f" ({e.direction})"
        lines.append(line)
    yield out_text("\n".join(lines))
