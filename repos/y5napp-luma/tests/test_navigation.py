import pytest


@pytest.mark.asyncio
async def test_place_item_and_list(worlds, boxes):
    world = await worlds.add_world(name="TestWelt", description="")
    room = await boxes.add_box(
        world_id=world.id, parent_id=None, name="Wohnzimmer",
        description="", portable=False,
    )

    current_world = world.id
    current_box = room.id

    item = await boxes.add_box(
        world_id=world.id, parent_id=room.id, name="Schrank",
        description="", portable=True,
    )
    assert item.portable is True

    items = await boxes.list_boxes(world_id=world.id, parent_id=room.id)
    portables = [b for b in items if b.portable]
    assert len(portables) == 1
    assert portables[0].name == "Schrank"

    child = next((c for c in items if c.name.lower() == "schrank"), None)
    assert child is not None
    current_box = child.id

    box_after = await boxes.get_box(box_id=current_box)
    assert box_after is not None
    assert box_after.name == "Schrank"

    item2 = await boxes.add_box(
        world_id=world.id, parent_id=child.id, name="Hose",
        description="", portable=True,
    )
    assert item2.name == "Hose"

    contents = await boxes.list_boxes(world_id=world.id, parent_id=child.id)
    portables = [b for b in contents if b.portable]
    assert any(b.name == "Hose" for b in portables)

    assert not any(b.name == "Schrank" for b in portables)
