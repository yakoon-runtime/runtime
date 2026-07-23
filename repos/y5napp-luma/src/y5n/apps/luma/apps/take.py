from y5n.sdk import context, io, ports


async def main():
    current_box = context.session().data.get("luma.current_box")
    current_world = context.session().data.get("luma.current_world")
    if not current_box or not current_world:
        await io.write("You are not inside any box.")
        return

    name = context.request().arg(0)
    if not name:
        await io.write("Take what?")
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

    inv_id = context.session().data.get("luma.inventory_id")
    if not inv_id:
        inv = await boxes.add_box(
            world_id=current_world,
            parent_id=None,
            name="_inventory",
            description="",
            portable=False,
        )
        await ports.get("session").update(patch={"data": {"luma.inventory_id": inv.id}})
        inv_id = inv.id

    await boxes.move_box(box_id=item.id, new_parent_id=inv_id)
    await io.write(f"Taken '{name}'.")
