import pytest


@pytest.mark.asyncio
async def test_world_lifecycle(worlds):
    w = await worlds.add_world(name="TestWelt", description="A test world")
    assert w.name == "TestWelt"
    assert w.description == "A test world"
    assert w.id is not None

    found = await worlds.get_world_by_name(name="TestWelt")
    assert found is not None
    assert found.id == w.id

    found = await worlds.get_world(world_id=w.id)
    assert found is not None
    assert found.name == "TestWelt"

    await worlds.update_world(world_id=w.id, name="NeueWelt", description="Updated")
    edited = await worlds.get_world(world_id=w.id)
    assert edited.name == "NeueWelt"
    assert edited.description == "Updated"

    await worlds.add_world(name="Other", description="")
    with pytest.raises(ValueError):
        await worlds.add_world(name="Other", description="")

    all_w = await worlds.list_worlds()
    assert len(all_w) >= 2

    await worlds.delete_world(world_id=w.id)
    assert await worlds.get_world(world_id=w.id) is None

    w2 = await worlds.add_world(name="WithEntry", description="")
    updated = await worlds.set_entry(world_id=w2.id, box_id="42")
    assert updated.entry_box_id == "42"
