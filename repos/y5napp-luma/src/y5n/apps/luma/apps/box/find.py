from y5n.sdk import context, io, ports


async def main():
    name = context.request().arg(0)
    world_ref = context.request().option("world")

    if not name:
        await io.write("Find what?")
        return
    if not world_ref:
        await io.write("Error: --world is required.")
        return

    worlds = ports.get("luma.world.service")
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(name=world_ref)
        if w is None:
            await io.write("World not found.")
            return
        world_id = w.id

    boxes = ports.get("luma.box.service")
    box = await boxes.find_box(world_id=world_id, name=name)
    if box is None:
        await io.write(f"Nothing named '{name}' found.")
        return

    path = await _resolve_path(boxes, box.id)
    await io.write(f"Found: {'/'.join(path)}")


async def _resolve_path(boxes, box_id) -> list[str]:
    names = []
    current = box_id
    while current is not None:
        b = await boxes.get_box(box_id=current)
        if b is None:
            break
        names.append(b.name)
        current = b.parent_id
    names.reverse()
    return names
