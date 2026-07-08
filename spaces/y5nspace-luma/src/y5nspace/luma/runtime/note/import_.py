from __future__ import annotations

import json

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

from ...services.contracts import NoteService


async def run(space: NodeSpace):
    file_path = space.request.option("file")

    try:
        with open(file_path) as f:
            items = json.load(f)
    except Exception as e:
        yield out_text(f"Error: {e}")
        return

    if not isinstance(items, list):
        yield out_text("Error: JSON must be an array of objects.")
        return

    notes = space.ports.get(NoteService)
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
        yield out_text("Import completed.\n\n  nothing to import")
        return

    yield out_text(f"Import completed.\n\n  {created} created\n  {updated} updated")
