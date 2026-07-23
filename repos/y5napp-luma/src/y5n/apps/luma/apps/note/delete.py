from y5n.sdk import context, io, ports, session


async def main():
    name = context.request().arg(0)
    if not name:
        await io.write("Error: note name is required.")
        return

    notes = ports.get("luma.note.service")
    note = await notes.find_note_by_name(name=name)
    if note is None:
        await io.write(f"Note '{name}' not found.")
        return

    try:
        await notes.delete_note(note_id=note.id)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Note '{name}' deleted.")
