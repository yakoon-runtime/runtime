from __future__ import annotations

import pytest
from y5n.runtime.engine.flow.channel import Scope
from y5n.runtime.engine.flow.dsl import receive, start_task
from y5n.runtime.engine.flow.primitives import AwaitEvent, Outcome, Stop


@pytest.mark.asyncio
async def test_start_task_result_routing(harness):
    """start_task dispatches a background OS process.
    The result arrives on the SESSION channel."""

    received: list[object] = []

    async def caller(ctx):
        from uuid import uuid4

        ch = uuid4().hex
        yield start_task("python3", channel=ch, args=["-c", "print(42)"])
        yield Outcome()

        event = yield receive(ch, scope=Scope.SESSION)
        received.append(event.payload)
        yield Outcome()

    flow = await harness.start(caller)

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)

    # Simulate task completion (real subprocess tested in integration)
    harness.send_session(
        outcome.control.channel,
        {"returncode": 0, "stdout": "42\n", "stderr": ""},
    )

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)

    assert received == [{"returncode": 0, "stdout": "42\n", "stderr": ""}]
