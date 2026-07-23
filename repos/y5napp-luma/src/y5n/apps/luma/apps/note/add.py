from y5n.sdk import context, io, ports, session


async def main():
    name = context.request().arg(0)
    content = context.request().option("content") or ""

    if not name:
        await io.write("Error: note name is required.")
        return

    notes = ports.get("luma.note.service")
    try:
        note = await notes.add_note(name=name, content=content)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Note '{note.name}' created.")
