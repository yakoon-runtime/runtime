from y5n.sdk import context, io, ports, session

import json


async def main():
    file_path = context.request().option("file")

    try:
        with open(file_path) as f:
            items = json.load(f)
    except Exception as e:
        await io.write(f"Error: {e}")
        return

    if not isinstance(items, list):
        await io.write("Error: JSON must be an array of objects.")
        return

    notes = ports.get("luma.note.service")
    created = 0
    updated = 0

    for item in items:
        name = item.get("name") if isinstance(item, dict) else None
        content = item.get("content", "") if isinstance(item, dict) else None

        if not name:
            continue

        existing = await notes.find_note_by_name(name)
        if existing:
            await notes.update_note(
                note_id=existing.id, name=existing.name, content=content
            )
            updated += 1
        else:
            await notes.add_note(name=name, content=content)
            created += 1

    total = created + updated
    if total == 0:
        await io.write("Import completed.\n\n  nothing to import")
        return

    yield out_text(f"Import completed.\n\n  {created} created\n  {updated} updated")
