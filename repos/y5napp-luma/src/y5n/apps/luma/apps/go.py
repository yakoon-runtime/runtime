from y5n.sdk import context, io, ports, session


async def main():
    current_box = session.get("luma.current_box")
    current_world = session.get("luma.current_world")
    if not current_box:
        await io.write("You are not inside any box.")
        return

    ref = context.request().arg(0) or ""
    if not ref:
        await io.write("Go where?")
        return

    boxes = ports.get("luma.box.service")

    if ref == "..":
        box = await boxes.get_box(current_box)
        if box is None or box.parent_id is None:
            await io.write("Cannot go up from here.")
            return
        parent = await boxes.get_box(box.parent_id)
        session.set("luma.current_box", box.parent_id)
        await io.write(f"{parent.name if parent else '..'}")
        return

    children = await boxes.list_boxes(world_id=current_world, parent_id=current_box)
    child = next((c for c in children if c.name.lower() == ref.lower()), None)
    if child is not None:
        session.set("luma.current_box", child.id)
        await io.write(f"{child.name}")
        return

    exits = ports.get("luma.exit.service")
    from_here = await exits.find_from(current_box)

    by_name = [e for e in from_here if e.name.lower() == ref.lower()]
    if len(by_name) == 1:
        e = by_name[0]
    elif len(by_name) > 1:
        await io.write(f"Multiple exits named '{ref}' from here.")
        return
    else:
        by_dir = [e for e in from_here if e.direction.lower() == ref.lower()]
        if len(by_dir) == 0:
            await io.write(f"Nothing leads '{ref}' from here.")
            return
        if len(by_dir) > 1:
            names = ", ".join(e.name or e.direction for e in by_dir)
            await io.write(f"Multiple exits lead '{ref}': {names}. Use a name.")
            return
        e = by_dir[0]

    target = await boxes.get_box(e.target_box_id)
    if target is None:
        await io.write(f"Exit leads nowhere (box #{e.target_box_id} missing).")
        return

    session.set("luma.current_box", target.id)
    await io.write(f"{target.name}")
