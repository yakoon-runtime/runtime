from y5n.sdk import context, io, ports, session


async def main():
    current_box = session.get("luma.current_box")
    current_world = session.get("luma.current_world")
    if not current_box or not current_world:
        await io.write("You are not inside any box.")
        return

    name = context.request().arg(0)
    description = context.request().option("description") or ""
    parent_ref = context.request().option("box")

    if not name:
        await io.write("Place what?")
        return

    parent_id = current_box
    if parent_ref:
        boxes = ports.get("luma.box.service")
        items = await boxes.list_boxes(world_id=current_world, parent_id=current_box)
        target = next((b for b in items if b.name.lower() == parent_ref.lower()), None)
        if target is None:
            await io.write(f"Box '{parent_ref}' not found here.")
            return
        parent_id = target.id

    boxes = ports.get("luma.box.service")
    try:
        box = await boxes.add_box(
            world_id=current_world,
            parent_id=parent_id,
            name=name,
            description=description,
            portable=True,
        )
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Placed '{box.name}'.")
