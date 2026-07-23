from y5n.sdk import context, io, ports, session


async def main():
    notes = ports.get("luma.note.service")
    unplaced = await notes.inbox()

    if not unplaced:
        await io.write("Inbox empty.")
        return

    lines = ["Inbox:"]
    for n in unplaced:
        lines.append(f"  #{n.id} {n.name}")
    await io.write("\n".join(lines))
