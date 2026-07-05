from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, ExitService


async def run(space: NodeSpace):
    current_box = space.session.get_data("luma.current_box")
    current_world = space.session.get_data("luma.current_world")
    if not current_box:
        yield out_text("You are not inside any box.")
        return

    ref = space.request.arg(0) or ""
    if not ref:
        yield out_text("Go where?")
        return

    boxes = space.ports.get(BoxService)

    # 0. go up (parent)
    if ref == "..":
        box = await boxes.get_box(current_box)
        if box is None or box.parent_id is None:
            yield out_text("Cannot go up from here.")
            return
        parent = await boxes.get_box(box.parent_id)
        space.session.set_data("luma.current_box", box.parent_id)
        yield out_text(f"{parent.name if parent else '..'}")
        return

    # 1. look for a child box (container / parent relation)
    children = await boxes.list_boxes(world_id=current_world, parent_id=current_box)
    child = next((c for c in children if c.name.lower() == ref.lower()), None)
    if child is not None:
        space.session.set_data("luma.current_box", child.id)
        yield out_text(f"{child.name}")
        return

    # 2. look for an exit
    exits = space.ports.get(ExitService)
    from_here = await exits.find_from(current_box)

    # exact name match
    by_name = [e for e in from_here if e.name.lower() == ref.lower()]
    if len(by_name) == 1:
        exit = by_name[0]
    elif len(by_name) > 1:
        yield out_text(f"Multiple exits named '{ref}' from here.")
        return
    else:
        # exact direction match
        by_dir = [e for e in from_here if e.direction.lower() == ref.lower()]
        if len(by_dir) == 0:
            yield out_text(f"Nothing leads '{ref}' from here.")
            return
        if len(by_dir) > 1:
            names = ", ".join(e.name or e.direction for e in by_dir)
            yield out_text(f"Multiple exits lead '{ref}': {names}. Use a name.")
            return
        exit = by_dir[0]

    boxes = space.ports.get(BoxService)
    target = await boxes.get_box(exit.target_box_id)
    if target is None:
        yield out_text(f"Exit leads nowhere (box #{exit.target_box_id} missing).")
        return

    space.session.set_data("luma.current_box", target.id)
    yield out_text(f"{target.name}")
