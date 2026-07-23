from y5n.sdk import context, io, ports, session


async def main():
    current_world = session.get("luma.current_world")
    current_box = session.get("luma.current_box")

    if current_world is None and current_box is None:
        await io.write("Nowhere to leave.")
        return

    session.set("luma.current_world", None)
    session.set("luma.current_box", None)

    parts = []
    if current_world:
        parts.append(f"'{current_world}'")
    if current_box:
        parts.append(f"box #{current_box}")
    await io.write(f"Left {' '.join(parts)}.")
