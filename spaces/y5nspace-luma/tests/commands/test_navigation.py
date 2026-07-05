import pytest
from y5n.base.nodes.request import Request
from y5nspace.luma.services.contracts import BoxService, WorldService


@pytest.mark.asyncio
async def test_place_and_look(fresh_space):
    session, space = fresh_space
    worlds = space.ports.get(WorldService)
    world = await worlds.add_world(name="TestWelt", description="")
    boxes = space.ports.get(BoxService)

    room = await boxes.add_box(
        world_id=world.id,
        parent_id=None,
        name="Wohnzimmer",
        description="",
        portable=False,
    )
    session.set_data("luma.current_world", world.id)
    session.set_data("luma.current_box", room.id)

    # place Schrank
    space.request = Request(command="test", tokens=["Schrank"], payload=None, lang="de")
    from y5nspace.luma.runtime.nav.place import run as place

    outcomes = [o async for o in place(space)]
    assert any("Placed" in str(o) for o in outcomes)

    # go into Schrank
    space.request = Request(command="test", tokens=["Schrank"], payload=None, lang="de")
    from y5nspace.luma.runtime.nav.go import run as go

    outcomes = [o async for o in go(space)]
    assert len(outcomes) > 0

    # verify current_box changed
    box_after = await boxes.get_box(session.get_data("luma.current_box"))
    assert box_after is not None
    assert box_after.name == "Schrank"

    # place Hose in Schrank
    space.request = Request(command="test", tokens=["Hose"], payload=None, lang="de")
    outcomes = [o async for o in place(space)]
    assert any("Placed" in str(o) for o in outcomes)

    # look shows Hose
    from y5nspace.luma.runtime.nav.look import run as look

    space.request = Request(command="test", tokens=[], payload=None, lang="de")
    outcomes = [o async for o in look(space)]
    text = " ".join(str(o) for o in outcomes)
    assert "Hose" in text, f"Expected Hose, got: {text}"
