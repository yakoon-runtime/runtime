from y5n.sdk import context, io, ports


async def main():
    current_box = context.session().data.get("luma.current_box")
    current_world = context.session().data.get("luma.current_world")
    if not current_box or not current_world:
        await io.write("You are not inside any box.")
        return

    name = context.request().arg(0)
    if not name:
        await io.write("Drop what?")
        return

    inv_id = context.session().data.get("luma.inventory_id")
    if not inv_id:
        await io.write("Nothing in inventory.")
        return

    boxes = ports.get("luma.box.service")
    items = await boxes.list_boxes(world_id=current_world, parent_id=inv_id)
    item = next((b for b in items if b.name.lower() == name.lower()), None)
    if item is None:
        await io.write(f"Nothing named '{name}' in inventory.")
        return

    await boxes.move_box(box_id=item.id, new_parent_id=current_box)
    await io.write(f"Dropped '{name}'.")
