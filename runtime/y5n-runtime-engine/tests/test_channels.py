from __future__ import annotations

import pytest
from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.dsl import receive
from y5n.runtime.api.flow.primitives import AwaitEvent, Pulse, Stop


@pytest.mark.asyncio
async def test_flow_channel_isolation(harness):
    """Two flows waiting on the same channel name — only the targeted
    flow receives the event."""

    results: list[str] = []

    async def handler_a():
        event = yield receive("form")
        results.append(f"a:{event.payload}")
        yield Pulse()

    async def handler_b():
        event = yield receive("form")
        results.append(f"b:{event.payload}")
        yield Pulse()

    flow_a = await harness.start(handler_a)
    flow_b = await harness.start(handler_b)

    pulse_a = await harness.run_until_blocked(flow_a)
    assert isinstance(pulse_a.control, AwaitEvent)
    assert pulse_a.control.channel == "form"
    assert pulse_a.control.scope == Scope.FLOW

    pulse_b = await harness.run_until_blocked(flow_b)
    assert isinstance(pulse_b.control, AwaitEvent)
    assert pulse_b.control.channel == "form"
    assert pulse_b.control.scope == Scope.FLOW

    # Push event to flow_a's channel only
    harness.send_flow(flow_a, "form", "hello a")

    pulse_a = await harness.run_until_blocked(flow_a)
    assert isinstance(pulse_a.control, Stop)

    assert results == ["a:hello a"]
    assert not flow_b.control.is_runnable(flow_b, harness.session)


@pytest.mark.asyncio
async def test_session_channel_cross_flow(harness):
    """Two flows communicating via SESSION scope channel."""

    results: list[str] = []

    async def sender():
        from y5n.runtime.api.flow.dsl import send
        from y5n.runtime.api.runtime import Event

        yield send("shared", Event(payload="cross-flow!"), scope=Scope.SESSION)
        yield Pulse()

    async def receiver():
        event = yield receive("shared", scope=Scope.SESSION)
        results.append(event.payload)
        yield Pulse()

    flow_b = await harness.start(receiver)
    pulse_b = await harness.run_until_blocked(flow_b)
    assert isinstance(pulse_b.control, AwaitEvent)

    flow_a = await harness.start(sender)
    pulse_a = await harness.run_until_blocked(flow_a)
    assert isinstance(pulse_a.control, Stop)

    assert flow_b.control.is_runnable(flow_b, harness.session)
    pulse_b = await harness.run_until_blocked(flow_b)
    assert isinstance(pulse_b.control, Stop)

    assert results == ["cross-flow!"]


@pytest.mark.asyncio
async def test_multiple_session_receivers(harness):
    """SESSION ist eine Shared Queue — nur einer von mehreren
    wartenden Flows empfängt ein Event."""

    received: list[tuple[str, object]] = []

    async def listener_a():
        event = yield receive("shared", scope=Scope.SESSION)
        received.append(("a", event.payload))
        yield Pulse()

    async def listener_b():
        event = yield receive("shared", scope=Scope.SESSION)
        received.append(("b", event.payload))
        yield Pulse()

    flow_a = await harness.start(listener_a)
    flow_b = await harness.start(listener_b)

    await harness.run_until_blocked(flow_a)
    await harness.run_until_blocked(flow_b)

    # One event on the SESSION channel → both see the mail,
    # but only one gets the event on pop
    harness.send_session("shared", "one")

    assert flow_a.control.is_runnable(flow_a, harness.session)
    assert flow_b.control.is_runnable(flow_b, harness.session)

    # Flow A pops the event and continues
    pulse = await harness.run_until_blocked(flow_a)
    assert isinstance(pulse.control, Stop)
    assert received == [("a", "one")]

    # Flow B pops None → blocked again
    assert not flow_b.control.is_runnable(flow_b, harness.session)

    # Second event → now Flow B gets it
    harness.send_session("shared", "two")
    pulse = await harness.run_until_blocked(flow_b)
    assert isinstance(pulse.control, Stop)
    assert received == [("a", "one"), ("b", "two")]


@pytest.mark.asyncio
async def test_schedule_waiting_wakes_flow(harness):
    """_schedule_waiting weckt einen auf SESSION-Channel wartenden Flow.

    Das Event liegt bereits im Channel, aber der Flow wird erst
    durch _schedule_waiting in die Ready-Queue gesetzt.
    """

    received = []

    async def handler():
        event = yield receive("wake_ch", scope=Scope.SESSION)
        received.append(event.payload)
        yield Pulse()

    flow = await harness.start(handler)
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, AwaitEvent)
    assert pulse.control.scope == Scope.SESSION

    # Flow blocked — simulate the state after scheduler.run() pop
    flow.scheduled = False
    assert not flow.scheduled

    # Event in the channel → flow is ready but not yet scheduled
    harness.send_session("wake_ch", "hello")
    assert flow.control.is_runnable(flow, harness.session)
    assert not flow.scheduled

    # _schedule_waiting wakes matching flows
    harness.scheduler._schedule_waiting(harness.session, "wake_ch")
    assert flow.scheduled

    # Flow processes the event
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    assert received == ["hello"]
