from y5n.sdk import context, io, ports


async def main():
    name_ref = context.request().arg(0)
    world_ref = context.request().option("world")

    if not name_ref:
        await io.write("Error: box name is required.")
        return
    if not world_ref:
        await io.write("Error: --world is required.")
        return

    worlds = ports.get("luma.world.service")
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(name=world_id)
        if w is None:
            await io.write("World not found.")
            return
        world_id = w.id

    boxes = ports.get("luma.box.service")
    box = await boxes.find_box(world_id=world_id, name=name_ref)
    if box is None:
        await io.write(f"Box '{name_ref}' not found.")
        return

    world = await worlds.get_world(world_id=box.world_id)

    lines = [
        f"Box #{box.id}",
        f"  Name: {box.name}",
    ]
    if world:
        lines.append(f"  World: {world.name} (#{world.id})")
    else:
        lines.append(f"  World: #{box.world_id}")
    if box.parent_id:
        lines.append(f"  Parent: #{box.parent_id}")
    if box.description:
        lines.append(f"  Description: {box.description}")
    await io.write("\n".join(lines))
