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


@pytest.mark.asyncio
async def test_multiple_session_receivers(harness):
    """SESSION ist eine Shared Queue — nur einer von mehreren
    wartenden Flows empfängt ein Event."""

    received: list[tuple[str, object]] = []

    async def listener_a(ctx):
        event = yield receive("shared", scope=Scope.SESSION)
        received.append(("a", event.payload))
        yield Outcome()

    async def listener_b(ctx):
        event = yield receive("shared", scope=Scope.SESSION)
        received.append(("b", event.payload))
        yield Outcome()

    flow_a = await harness.start(listener_a)
    flow_b = await harness.start(listener_b)

    await harness.run_until_blocked(flow_a)
    await harness.run_until_blocked(flow_b)

    # Ein Event auf den SESSION-Channel → beide sehen Mail,
    # aber nur einer kriegt das Event beim Pop
    harness.send_session("shared", "one")

    assert flow_a.control.is_runnable(flow_a, harness.session)
    assert flow_b.control.is_runnable(flow_b, harness.session)

    # Flow A poppt das Event und läuft durch
    outcome = await harness.run_until_blocked(flow_a)
    assert isinstance(outcome.control, Stop)
    assert received == [("a", "one")]

    # Flow B poppt None → ist wieder blockiert
    assert not flow_b.control.is_runnable(flow_b, harness.session)

    # Zweites Event → jetzt kriegt Flow B es
    harness.send_session("shared", "two")
    outcome = await harness.run_until_blocked(flow_b)
    assert isinstance(outcome.control, Stop)
    assert received == [("a", "one"), ("b", "two")]


@pytest.mark.asyncio
async def test_schedule_waiting_wakes_flow(harness):
    """_schedule_waiting weckt einen auf SESSION-Channel wartenden Flow.

    Das Event liegt bereits im Channel, aber der Flow wird erst
    durch _schedule_waiting in die Ready-Queue gesetzt.
    """

    received = []

    async def handler(ctx):
        event = yield receive("wake_ch", scope=Scope.SESSION)
        received.append(event.payload)
        yield Outcome()

    flow = await harness.start(handler)
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)
    assert outcome.control.scope == Scope.SESSION

    # Flow blockiert — simuliere Zustand nach scheduler.run()-Pop
    flow.scheduled = False
    assert not flow.scheduled

    # Event im Channel → Flow ist rüstig, aber noch nicht scheduled
    harness.send_session("wake_ch", "hello")
    assert flow.control.is_runnable(flow, harness.session)
    assert not flow.scheduled

    # _schedule_waiting weckt passende Flows
    harness.scheduler._schedule_waiting(harness.session, "wake_ch")
    assert flow.scheduled

    # Flow verarbeitet das Event
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)
    assert received == ["hello"]
