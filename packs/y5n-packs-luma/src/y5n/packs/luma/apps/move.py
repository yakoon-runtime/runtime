from y5n.sdk import context, io, ports


async def main():
    current_box = context.session().data.get("luma.current_box")
    current_world = context.session().data.get("luma.current_world")
    if not current_box or not current_world:
        await io.write("You are not inside any box.")
        return

    name = context.request().arg(0)
    target_ref = context.request().option("box")

    if not name:
        await io.write("Move what?")
        return
    if not target_ref:
        await io.write("Move where? Use --box.")
        return

    boxes = ports.get("luma.box.service")
    items = await boxes.list_boxes(world_id=current_world, parent_id=current_box)
    item = next((b for b in items if b.name.lower() == name.lower()), None)
    if item is None:
        await io.write(f"Nothing named '{name}' here.")
        return
    if not item.portable:
        await io.write(f"'{name}' is not portable.")
        return

    target = next((b for b in items if b.name.lower() == target_ref.lower()), None)
    if target is None:
        await io.write(f"Box '{target_ref}' not found here.")
        return

    await boxes.move_box(box_id=item.id, new_parent_id=target.id)
    await io.write(f"Moved '{name}' into '{target.name}'.")
