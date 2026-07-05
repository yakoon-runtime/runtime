import pytest
from y5nspace.luma.services.contracts import BoxService, NoteService, WorldService


@pytest.mark.asyncio
async def test_note_lifecycle(fresh_space):
    session, space = fresh_space
    worlds = space.ports.get(WorldService)
    boxes = space.ports.get(BoxService)
    notes = space.ports.get(NoteService)

    world = await worlds.add_world(name="Welt", description="")
    room = await boxes.add_box(
        world_id=world.id, parent_id=None, name="Raum", description="", portable=False
    )

    # add
    n = await notes.add_note(name="Zeitlich", content="Zeitinseln nutzen.")
    assert n.name == "Zeitlich"
    assert n.content == "Zeitinseln nutzen."

    # find by name
    found = await notes.find_note_by_name("Zeitlich")
    assert found is not None
    assert found.id == n.id

    # edit
    await notes.update_note(
        note_id=n.id, name="Prioritäten", content="Wichtiges zuerst."
    )
    edited = await notes.get_note(n.id)
    assert edited.name == "Prioritäten"

    # link
    link = await notes.link(note_id=n.id, box_id=room.id)
    assert link.note_id == n.id
    assert link.box_id == room.id

    # notes for box
    box_notes = await notes.notes_for_box(room.id)
    assert len(box_notes) == 1
    assert box_notes[0].name == "Prioritäten"

    # inbox (linked → not in inbox)
    inbox = await notes.inbox()
    assert len(inbox) == 0

    # add unlinked note → appears in inbox
    n2 = await notes.add_note(name="Ideen", content="")
    inbox = await notes.inbox()
    assert len(inbox) == 1
    assert inbox[0].name == "Ideen"

    # list all
    all_n = await notes.list_notes()
    assert len(all_n) == 2

    # unlink
    await notes.unlink(n.id, room.id)
    box_notes = await notes.notes_for_box(room.id)
    assert len(box_notes) == 0

    # delete
    await notes.delete_note(n.id)
    assert await notes.get_note(n.id) is None

    # duplicate name blocked
    await notes.add_note(name="Unique", content="")
    with pytest.raises(ValueError):
        await notes.add_note(name="Unique", content="")
