from y5n.sdk import context, io, ports, session


async def main():
    name = context.request().arg(0)

    if not name:
        await io.write("Show which note?")
        return

    notes = ports.get("luma.note.service")
    note = await notes.find_note_by_name(name)
    if note is None:
        await io.write(f"Note '{name}' not found.")
        return

    await io.write(f"{note.name}\n\n{note.content}")
