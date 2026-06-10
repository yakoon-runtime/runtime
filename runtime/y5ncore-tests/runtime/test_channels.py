from __future__ import annotations

import pytest
from y5n.base.flow.channel import Scope
from y5n.base.flow.dsl import receive
from y5n.base.flow.primitives import AwaitEvent, Outcome, Stop


@pytest.mark.asyncio
async def test_flow_channel_isolation(harness):
    """Two flows waiting on the same channel name — only the targeted
    flow receives the event."""

    results: list[str] = []

    async def handler_a(ctx):
        event = yield receive("form")
        results.append(f"a:{event.payload}")
        yield Outcome()

    async def handler_b(ctx):
        event = yield receive("form")
        results.append(f"b:{event.payload}")
        yield Outcome()

    flow_a = await harness.start(handler_a)
    flow_b = await harness.start(handler_b)

    outcome_a = await harness.run_until_blocked(flow_a)
    assert isinstance(outcome_a.control, AwaitEvent)
    assert outcome_a.control.channel == "form"
    assert outcome_a.control.scope == Scope.FLOW

    outcome_b = await harness.run_until_blocked(flow_b)
    assert isinstance(outcome_b.control, AwaitEvent)
    assert outcome_b.control.channel == "form"
    assert outcome_b.control.scope == Scope.FLOW

    # Push event to flow_a's channel only
    harness.send_flow(flow_a, "form", "hello a")

    outcome_a = await harness.run_until_blocked(flow_a)
    assert isinstance(outcome_a.control, Stop)

    assert results == ["a:hello a"]
    assert not flow_b.control.is_runnable(flow_b, harness.session)


@pytest.mark.asyncio
async def test_session_channel_cross_flow(harness):
    """Two flows communicating via SESSION scope channel."""

    results: list[str] = []

    async def sender(ctx):
        from y5n.base.flow.dsl import send
        from y5n.base.runtime import Event

        yield send("shared", Event(payload="cross-flow!"), scope=Scope.SESSION)
        yield Outcome()

    async def receiver(ctx):
        event = yield receive("shared", scope=Scope.SESSION)
        results.append(event.payload)
        yield Outcome()

    flow_b = await harness.start(receiver)
    outcome_b = await harness.run_until_blocked(flow_b)
    assert isinstance(outcome_b.control, AwaitEvent)

    flow_a = await harness.start(sender)
    outcome_a = await harness.run_until_blocked(flow_a)
    assert isinstance(outcome_a.control, Stop)

    assert flow_b.control.is_runnable(flow_b, harness.session)
    outcome_b = await harness.run_until_blocked(flow_b)
    assert isinstance(outcome_b.control, Stop)

    assert results == ["cross-flow!"]
