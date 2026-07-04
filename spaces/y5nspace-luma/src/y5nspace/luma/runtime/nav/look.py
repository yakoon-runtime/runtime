from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import BoxService, ExitService, WorldService


async def run(space: NodeSpace):
    current_box = space.session.data.get("luma.current_box")
    current_world = space.session.data.get("luma.current_world")

    if not current_box:
        yield out_text("You are not inside any box. Use 'enter' first.")
        return

    boxes = space.ports.get(BoxService)
    box = await boxes.get_box(current_box)
    if box is None:
        yield out_text("Current box not found.")
        return

    worlds = space.ports.get(WorldService)
    world = await worlds.get_world(current_world)

    lines = [f"[{box.name}]"]
    if box.description:
        lines.append(f"  {box.description}")

    exits = space.ports.get(ExitService)
    from_here = await exits.find_from(box.id)

    if from_here:
        lines.append("")
        lines.append("Exits:")
        for e in from_here:
            target = await boxes.get_box(e.target_box_id)
            target_name = target.name if target else f"#{e.target_box_id}"
            label = e.name or e.direction or "?"
            if e.direction and e.name:
                lines.append(f"  {e.direction}: {label} → {target_name}")
            else:
                lines.append(f"  {label} → {target_name}")

    yield out_text("\n".join(lines))
