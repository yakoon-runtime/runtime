from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from .ports import BOX_SERVICE, WORLD_SERVICE


async def _resolve_path(boxes, box_id) -> list[str]:
    names = []
    current = box_id
    while current is not None:
        b = await boxes.get_box(current)
        if b is None:
            break
        names.append(b.name)
        current = b.parent_id
    names.reverse()
    return names


async def run(space: NodeSpace):
    name = space.request.arg(0)
    world_ref = space.request.option("world")

    if not name:
        yield out_text("Find what?")
        return
    if not world_ref:
        yield out_text("Error: --world is required.")
        return

    worlds = space.ports.get(WORLD_SERVICE)
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(world_ref)
        if w is None:
            yield out_text("World not found.")
            return
        world_id = w.id

    boxes = space.ports.get(BOX_SERVICE)
    box = await boxes.find_box(world_id=world_id, name=name)
    if box is None:
        yield out_text(f"Nothing named '{name}' found.")
        return

    path = await _resolve_path(boxes, box.id)
    yield out_text(f"Found: {'/'.join(path)}")
