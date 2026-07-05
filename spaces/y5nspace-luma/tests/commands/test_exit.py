import pytest
from y5nspace.luma.services.contracts import BoxService, ExitService, WorldService


@pytest.mark.asyncio
async def test_exit_lifecycle(fresh_space):
    session, space = fresh_space
    worlds = space.ports.get(WorldService)
    boxes = space.ports.get(BoxService)
    exits = space.ports.get(ExitService)

    world = await worlds.add_world(name="Welt", description="")
    raum_a = await boxes.add_box(
        world_id=world.id, parent_id=None, name="A", description="", portable=False
    )
    raum_b = await boxes.add_box(
        world_id=world.id, parent_id=None, name="B", description="", portable=False
    )

    # connect
    e = await exits.connect(
        world_id=world.id,
        source_box_id=raum_a.id,
        target_box_id=raum_b.id,
        name="Tür",
        direction="norden",
    )
    assert e.name == "Tür"
    assert e.source_box_id == raum_a.id
    assert e.target_box_id == raum_b.id
    assert e.direction == "norden"

    # find from
    from_a = await exits.find_from(raum_a.id)
    assert len(from_a) == 1
    assert from_a[0].target_box_id == raum_b.id

    # find to
    to_b = await exits.find_to(raum_b.id)
    assert len(to_b) == 1
    assert to_b[0].source_box_id == raum_a.id

    # list in world
    all_exits = await exits.list_exits(world_id=world.id)
    assert len(all_exits) == 1

    # get by id
    got = await exits.get_exit(e.id)
    assert got is not None
    assert got.name == "Tür"

    # name uniqueness per source box
    with pytest.raises(ValueError):
        await exits.connect(
            world_id=world.id,
            source_box_id=raum_a.id,
            target_box_id=raum_b.id,
            name="Tür",
        )

    # disconnect
    await exits.disconnect(e.id)
    from_a_after = await exits.find_from(raum_a.id)
    assert len(from_a_after) == 0
