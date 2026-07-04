from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, ExitService
from ...services.directions import Directions


async def run(space: NodeSpace):
    current_box = space.session.data.get("luma.current_box")
    current_world = space.session.data.get("luma.current_world")
    if not current_box or not current_world:
        yield out_text("You are not inside any box. Use 'enter' first.")
        return

    target_ref = space.request.arg(0)
    direction = space.request.option("direction") or ""
    via = space.request.option("via") or target_ref
    twoway = space.request.has_option("twoway")

    if not target_ref:
        yield out_text("Error: target name is required.")
        return

    boxes = space.ports.get(BoxService)
    exits = space.ports.get(ExitService)

    existing = await boxes.list_boxes(world_id=current_world, parent_id=None)
    target = next((b for b in existing if b.name.lower() == target_ref.lower()), None)

    if target is None:
        target = await boxes.add_box(
            world_id=current_world,
            parent_id=None,
            name=target_ref,
            description="",
        )

    await exits.connect(
        world_id=current_world,
        source_box_id=current_box,
        target_box_id=target.id,
        name=via,
        direction=direction,
    )

    lines = [f"Connected to '{target.name}' via '{via}'."]

    if twoway:
        rev_dir = Directions.opposite(direction) if direction else ""
        await exits.connect(
            world_id=current_world,
            source_box_id=target.id,
            target_box_id=current_box,
            name=via,
            direction=rev_dir,
        )
        lines.append("  Reverse exit created.")

    yield out_text("\n".join(lines))
