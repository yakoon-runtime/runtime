import pytest
from src.libs import ports as luma_ports


@pytest.mark.asyncio
async def test_world_lifecycle(fresh_space):
    session, space = fresh_space
    worlds = space.ports.get(luma_ports.WORLD_SERVICE)

    w = await worlds.add_world(name="TestWelt", description="A test world")
    assert w.name == "TestWelt"
    assert w.description == "A test world"
    assert w.id is not None

    found = await worlds.get_world_by_name("TestWelt")
    assert found is not None
    assert found.id == w.id

    found = await worlds.get_world(w.id)
    assert found is not None
    assert found.name == "TestWelt"

    await worlds.update_world(world_id=w.id, name="NeueWelt", description="Updated")
    edited = await worlds.get_world(w.id)
    assert edited.name == "NeueWelt"
    assert edited.description == "Updated"

    await worlds.add_world(name="Other", description="")
    with pytest.raises(ValueError):
        await worlds.add_world(name="Other", description="")

    all_w = await worlds.list_worlds()
    assert len(all_w) >= 2

    await worlds.delete_world(w.id)
    assert await worlds.get_world(w.id) is None

    w2 = await worlds.add_world(name="WithEntry", description="")
    updated = await worlds.set_entry(world_id=w2.id, box_id="42")
    assert updated.entry_box_id == "42"
