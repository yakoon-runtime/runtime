from y5n.sdk import context, io, ports


async def main():
    world_ref = context.request().option("world")
    parent_id = context.request().option("parent")

    worlds = ports.get("luma.world.service")
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(name=world_id)
        if w is None:
            await io.write("World not found.")
            return
        world_id = w.id

    boxes = ports.get("luma.box.service")
    all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=parent_id)

    if not all_boxes:
        await io.write("No boxes here.")
        return

    lines = ["Boxes:"]
    for b in all_boxes:
        desc = f" -- {b.description}" if b.description else ""
        lines.append(f"  #{b.id} {b.name}{desc}")
    await io.write("\n".join(lines))
