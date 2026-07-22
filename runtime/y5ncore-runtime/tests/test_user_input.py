from __future__ import annotations

import pytest
from y5n.runtime.api.flow.dsl import receive
from y5n.runtime.api.flow.primitives import AwaitEvent, Outcome, Stop
from y5n.runtime.api.nodes import Node
from y5n.runtime.api.runtime import Event
from y5n.runtime.machine.runner import Runner


@pytest.mark.asyncio
async def test_receive_user_input(harness):

    received = []

    async def handler(ctx):
        event = yield receive()
        received.append(event.payload)

    flow = await harness.start(handler)

    outcome = await harness.run_until_blocked(flow)

    assert isinstance(outcome.control, AwaitEvent)

    harness.send_user_input(flow, "hello")

    outcome = await harness.run_until_blocked(flow)

    assert isinstance(outcome.control, Stop)

    assert received == ["hello"]


def _make_runner(harness):
    """Helper: erzeugt einen Runner mit dispatchendem on_dispatch."""

    async def on_dispatch(*, session, event):
        flow = await harness.engine.dispatch(session=session, event=event)
        if flow:
            harness.scheduler.schedule_flow(flow, harness.session)

    return Runner(
        session=harness.session,
        on_dispatch=on_dispatch,
        on_schedule_flow=harness.scheduler.schedule_flow,
    )


@pytest.mark.asyncio
async def test_input_without_foreground_dispatches_new_flow(harness):
    """Ohne Foreground-Flow → Runner.on_input erzeugt neuen Flow via dispatch."""

    assert harness.session.foreground_flow is None

    async def handler(ctx):
        yield Outcome()

    node = Node(key="test", run=handler)

    def parse_input(*, event):
        cmd, *rest = event.payload.strip().split()
        return cmd, rest, []

    def resolve_node(*, key, tokens, session, strict=True):
        if key == "test":
            return node, tokens or []
        return None, tokens or []

    harness.engine.on_parse_input = parse_input
    harness.engine.on_resolve_command = resolve_node

    runner = _make_runner(harness)
    await runner.on_input(Event(payload="test"))

    flows = list(harness.session.flows())
    assert len(flows) == 1
    flow = flows[0]
    assert flow.node is node

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)


@pytest.mark.asyncio
async def test_input_with_foreground_pushes_to_flow(harness):
    """Mit Foreground-Flow → Runner.on_input pusht Event an den Fokus."""

    received = []

    async def fg_handler(ctx):
        event = yield receive()
        received.append(event.payload)

    fg = await harness.start(fg_handler)
    outcome = await harness.run_until_blocked(fg)
    assert isinstance(outcome.control, AwaitEvent)

    # Fokus setzen (wie runner.py line 39-43: flow = session.foreground_flow)
    harness.session.set_foreground_flow(fg.id)
    assert harness.session.foreground_flow is fg

    runner = _make_runner(harness)
    await runner.on_input(Event(payload="hello"))

    # Der Foreground-Flow wurde aufgeweckt und läuft weiter
    outcome = await harness.run_until_blocked(fg)
    assert isinstance(outcome.control, Stop)
    assert received == ["hello"]
