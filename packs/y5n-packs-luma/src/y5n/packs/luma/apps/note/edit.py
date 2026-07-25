from y5n.sdk import context, io, ports


async def main():
    name = context.request().arg(0)
    new_name = context.request().option("new-name")
    content = context.request().option("content")

    notes = ports.get("luma.note.service")
    note = await notes.find_note_by_name(name=name)
    if note is None:
        await io.write(f"Note '{name}' not found.")
        return

    try:
        await notes.update_note(
            note_id=note.id,
            name=new_name or note.name,
            content=content or note.content,
        )
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Note '{name}' updated.")
