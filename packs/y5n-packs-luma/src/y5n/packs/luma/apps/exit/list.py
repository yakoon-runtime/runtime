from y5n.sdk import context, io, ports


async def main():
    world_ref = context.request().option("world")
    box_ref = context.request().option("box")

    worlds = ports.get("luma.world.service")
    world_id = world_ref
    if not world_id.isdigit():
        w = await worlds.get_world_by_name(name=world_id)
        if w is None:
            await io.write("World not found.")
            return
        world_id = w.id

    exits = ports.get("luma.exit.service")
    boxes = ports.get("luma.box.service")

    if box_ref:
        all_boxes = await boxes.list_boxes(world_id=world_id, parent_id=None)
        box_id = next(
            (b.id for b in all_boxes if b.name.lower() == box_ref.lower()), None
        )
        if box_id is None:
            await io.write(f"Box '{box_ref}' not found.")
            return
        exits_list = await exits.find_from(box_id=box_id)
    else:
        exits_list = await exits.list_exits(world_id=world_id)

    if not exits_list:
        await io.write("No exits.")
        return

    lines = ["Exits:"]
    for e in exits_list:
        source = await boxes.get_box(box_id=e.source_box_id)
        target = await boxes.get_box(box_id=e.target_box_id)
        src_name = source.name if source else f"#{e.source_box_id}"
        tgt_name = target.name if target else f"#{e.target_box_id}"
        line = f"  #{e.id} {e.name or '?'}: {src_name} -> {tgt_name}"
        if e.direction:
            line += f" ({e.direction})"
        lines.append(line)
    await io.write("\n".join(lines))
