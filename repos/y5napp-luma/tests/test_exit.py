import pytest


@pytest.mark.asyncio
async def test_exit_lifecycle(worlds, boxes, exits):
    world = await worlds.add_world(name="Welt", description="")
    raum_a = await boxes.add_box(
        world_id=world.id, parent_id=None, name="A", description="", portable=False
    )
    raum_b = await boxes.add_box(
        world_id=world.id, parent_id=None, name="B", description="", portable=False
    )

    e = await exits.connect(
        world_id=world.id, source_box_id=raum_a.id, target_box_id=raum_b.id,
        name="Tür", direction="norden",
    )
    assert e.name == "Tür"
    assert e.source_box_id == raum_a.id
    assert e.target_box_id == raum_b.id
    assert e.direction == "norden"

    from_a = await exits.find_from(box_id=raum_a.id)
    assert len(from_a) == 1
    assert from_a[0].target_box_id == raum_b.id

    to_b = await exits.find_to(box_id=raum_b.id)
    assert len(to_b) == 1
    assert to_b[0].source_box_id == raum_a.id

    all_exits = await exits.list_exits(world_id=world.id)
    assert len(all_exits) == 1

    got = await exits.get_exit(exit_id=e.id)
    assert got is not None
    assert got.name == "Tür"

    with pytest.raises(ValueError):
        await exits.connect(
            world_id=world.id, source_box_id=raum_a.id,
            target_box_id=raum_b.id, name="Tür",
        )

    await exits.disconnect(exit_id=e.id)
    from_a_after = await exits.find_from(box_id=raum_a.id)
    assert len(from_a_after) == 0
