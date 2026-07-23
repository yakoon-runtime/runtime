from y5n.sdk import context, io, ports


async def main():
    current_world = context.session().data.get("luma.current_world")
    current_box = context.session().data.get("luma.current_box")

    if current_world is None and current_box is None:
        await io.write("Nowhere to leave.")
        return

    await ports.get("session").update(patch={"data": {"luma.current_world": None}})
    await ports.get("session").update(patch={"data": {"luma.current_box": None}})

    parts = []
    if current_world:
        parts.append(f"'{current_world}'")
    if current_box:
        parts.append(f"box #{current_box}")
    await io.write(f"Left {' '.join(parts)}.")
