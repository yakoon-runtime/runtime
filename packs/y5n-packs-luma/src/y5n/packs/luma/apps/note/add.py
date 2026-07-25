from y5n.sdk import context, io, ports


async def main():
    name = context.request().arg(0)
    content = context.request().option("content") or ""

    notes = ports.get("luma.note.service")
    try:
        note = await notes.add_note(name=name, content=content)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Note '{note.name}' created.")
