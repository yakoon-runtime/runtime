from __future__ import annotations

import pytest
from y5n.base.flow.dsl import receive
from y5n.base.flow.primitives import AwaitEvent, Stop


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
