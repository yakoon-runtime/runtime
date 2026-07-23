from y5n.sdk import context, io, ports, session


async def main():
    current_world = session.get("luma.current_world")
    inv_id = session.get("luma.inventory_id")

    if not inv_id or not current_world:
        await io.write("Nothing in inventory.")
        return

    boxes = ports.get("luma.box.service")
    items = await boxes.list_boxes(world_id=current_world, parent_id=inv_id)

    if not items:
        await io.write("Nothing in inventory.")
        return

    lines = ["Inventory:"]
    for b in items:
        parts = [f"  {b.name}"]
        if b.description:
            parts.append(f" - {b.description}")
        lines.append("".join(parts))
    await io.write("\n".join(lines))
