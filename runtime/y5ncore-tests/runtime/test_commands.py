from __future__ import annotations

import pytest
from y5n.base.flow.channel import Scope
from y5n.base.flow.dsl import receive, start_cmd
from y5n.base.flow.primitives import AwaitEvent, Outcome, Stop
from y5n.base.nodes import Node


@pytest.mark.asyncio
async def test_command_channel_contract(harness):
    """start_cmd dispatches a sub-flow; the caller receives
    the result on the configured SESSION channel."""

    received: list[object] = []

    async def sub_flow(ctx):
        from y5n.base.flow.dsl import out
        from y5n.base.projection import Projection

        yield out(Projection.create(blocks=[]))
        yield Outcome()

    async def caller(ctx):
        from uuid import uuid4

        ch = uuid4().hex
        yield start_cmd("test", channel=ch)
        yield Outcome()

        event = yield receive(ch, scope=Scope.SESSION)
        received.append(event.payload)
        yield Outcome()

    sub_node = Node(key="test", run=sub_flow)

    async def resolve(parent, key, tokens, session):
        return sub_node, tokens or []

    harness.engine.on_resolve_node = resolve

    flow = await harness.start(caller)

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)

    # Simulate sub-flow result on the channel
    harness.send_session(outcome.control.channel, {"done": True})

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)

    assert received == [{"done": True}]
