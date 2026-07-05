import pytest
from y5nspace.luma.services.contracts import BoxService, WorldService


@pytest.mark.asyncio
async def test_box_lifecycle(fresh_space):
    session, space = fresh_space
    worlds = space.ports.get(WorldService)
    boxes = space.ports.get(BoxService)

    world = await worlds.add_world(name="Welt", description="")

    # add
    b = await boxes.add_box(
        world_id=world.id,
        parent_id=None,
        name="Wohnzimmer",
        description="Main room",
        portable=False,
    )
    assert b.name == "Wohnzimmer"
    assert b.id is not None
    assert b.portable is False

    # get by id
    got = await boxes.get_box(b.id)
    assert got is not None
    assert got.name == "Wohnzimmer"

    # list root boxes
    root = await boxes.list_boxes(world_id=world.id, parent_id=None)
    assert len(root) == 1
    assert root[0].name == "Wohnzimmer"

    # add child box (portable item)
    item = await boxes.add_box(
        world_id=world.id, parent_id=b.id, name="Tisch", description="", portable=True
    )
    assert item.portable is True

    # list children
    children = await boxes.list_boxes(world_id=world.id, parent_id=b.id)
    assert len(children) == 1
    assert children[0].name == "Tisch"

    # find by name
    found = await boxes.find_box(world_id=world.id, name="Tisch")
    assert found is not None
    assert found.id == item.id

    # update
    await boxes.update_box(box_id=b.id, name="Zimmer", description="Updated")
    updated = await boxes.get_box(b.id)
    assert updated.name == "Zimmer"

    # move
    assert updated.parent_id is None
    await boxes.move_box(item.id, None)
    moved = await boxes.get_box(item.id)
    assert moved.parent_id is None

    # delete
    await boxes.delete_box(b.id)
    assert await boxes.get_box(b.id) is None
