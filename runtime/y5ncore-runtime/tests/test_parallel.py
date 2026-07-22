from __future__ import annotations

import pytest
from y5n.runtime.engine.flow.channel import Scope
from y5n.runtime.engine.flow.dsl import receive, start_cmd, start_task
from y5n.runtime.engine.flow.primitives import AwaitEvent, Outcome, Stop


@pytest.mark.asyncio
async def test_multiple_commands_parallel(harness, effect_executor):
    """Mehrere start_cmd-Effects werden nacheinander dispatchet,
    bevor der Handler auf receive() blockiert."""

    received: list[object] = []

    async def caller(ctx):
        from uuid import uuid4

        ch_a = uuid4().hex
        ch_b = uuid4().hex
        yield start_cmd("cmd_a", channel=ch_a)
        yield start_cmd("cmd_b", channel=ch_b)
        yield Outcome()

        event = yield receive(ch_a, scope=Scope.SESSION)
        received.append(event.payload)
        event = yield receive(ch_b, scope=Scope.SESSION)
        received.append(event.payload)
        yield Outcome()

    flow = await harness.start(caller)

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)

    # Beide Commands wurden dispatchet, bevor der erste receive() blockte
    assert effect_executor.on_start_command.call_count == 2

    # Ergebnisse simulieren
    ch1 = outcome.control.channel
    harness.send_session(ch1, "first")
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)

    ch2 = outcome.control.channel
    harness.send_session(ch2, "second")
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)

    assert received == ["first", "second"]


@pytest.mark.asyncio
async def test_multiple_tasks_parallel(harness, effect_executor):
    """Mehrere start_task-Effects werden nacheinander dispatchet,
    bevor der Handler auf receive() blockiert."""

    received: list[object] = []

    async def caller(ctx):
        from uuid import uuid4

        ch_a = uuid4().hex
        ch_b = uuid4().hex
        yield start_task("echo", channel=ch_a, args=["hello"])
        yield start_task("echo", channel=ch_b, args=["world"])
        yield Outcome()

        event = yield receive(ch_a, scope=Scope.SESSION)
        received.append(event.payload)
        event = yield receive(ch_b, scope=Scope.SESSION)
        received.append(event.payload)
        yield Outcome()

    flow = await harness.start(caller)

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)

    # Beide Tasks wurden dispatchet, bevor der erste receive() blockte
    assert effect_executor.on_start_task.call_count == 2

    # Ergebnisse simulieren
    ch1 = outcome.control.channel
    harness.send_session(ch1, "result_a")
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)

    ch2 = outcome.control.channel
    harness.send_session(ch2, "result_b")
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)

    assert received == ["result_a", "result_b"]
