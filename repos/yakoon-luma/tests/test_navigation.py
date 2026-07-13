import pytest
from setup import ports as luma_ports


@pytest.mark.asyncio
async def test_place_item_and_list(fresh_space):
    session, space = fresh_space
    worlds = space.ports.get(luma_ports.WORLD_SERVICE)
    boxes = space.ports.get(luma_ports.BOX_SERVICE)

    world = await worlds.add_world(name="TestWelt", description="")
    room = await boxes.add_box(
        world_id=world.id,
        parent_id=None,
        name="Wohnzimmer",
        description="",
        portable=False,
    )
    session.set_data("luma.current_world", world.id)
    session.set_data("luma.current_box", room.id)

    # place a portable item (like the 'place' command does)
    item = await boxes.add_box(
        world_id=world.id,
        parent_id=room.id,
        name="Schrank",
        description="",
        portable=True,
    )
    assert item.portable is True

    # list items in current box (like 'look' command does)
    items = await boxes.list_boxes(world_id=world.id, parent_id=room.id)
    portables = [b for b in items if b.portable]
    assert len(portables) == 1
    assert portables[0].name == "Schrank"

    # go into child box (like 'go NAME' does)
    child = next((c for c in items if c.name.lower() == "schrank"), None)
    assert child is not None
    session.set_data("luma.current_box", child.id)

    box_after = await boxes.get_box(session.get_data("luma.current_box"))
    assert box_after is not None
    assert box_after.name == "Schrank"

    # place another item inside
    item2 = await boxes.add_box(
        world_id=world.id,
        parent_id=child.id,
        name="Hose",
        description="",
        portable=True,
    )
    assert item2.name == "Hose"

    # look shows Hose
    contents = await boxes.list_boxes(world_id=world.id, parent_id=child.id)
    portables = [b for b in contents if b.portable]
    assert any(b.name == "Hose" for b in portables)

    # verify Schrank contains Hose (not current box directly)
    assert not any(b.name == "Schrank" for b in portables)
