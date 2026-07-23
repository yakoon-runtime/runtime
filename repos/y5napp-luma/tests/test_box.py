import pytest


@pytest.mark.asyncio
async def test_box_lifecycle(worlds, boxes):
    world = await worlds.add_world(name="Welt", description="")

    b = await boxes.add_box(
        world_id=world.id, parent_id=None, name="Wohnzimmer",
        description="Main room", portable=False,
    )
    assert b.name == "Wohnzimmer"
    assert b.id is not None
    assert b.portable is False

    got = await boxes.get_box(box_id=b.id)
    assert got is not None
    assert got.name == "Wohnzimmer"

    root = await boxes.list_boxes(world_id=world.id, parent_id=None)
    assert len(root) == 1
    assert root[0].name == "Wohnzimmer"

    item = await boxes.add_box(
        world_id=world.id, parent_id=b.id, name="Tisch",
        description="", portable=True,
    )
    assert item.portable is True

    children = await boxes.list_boxes(world_id=world.id, parent_id=b.id)
    assert len(children) == 1
    assert children[0].name == "Tisch"

    found = await boxes.find_box(world_id=world.id, name="Tisch")
    assert found is not None
    assert found.id == item.id

    await boxes.update_box(box_id=b.id, name="Zimmer", description="Updated")
    updated = await boxes.get_box(box_id=b.id)
    assert updated.name == "Zimmer"

    assert updated.parent_id is None
    await boxes.move_box(box_id=item.id, new_parent_id=None)
    moved = await boxes.get_box(box_id=item.id)
    assert moved.parent_id is None

    await boxes.delete_box(box_id=b.id)
    assert await boxes.get_box(box_id=b.id) is None
