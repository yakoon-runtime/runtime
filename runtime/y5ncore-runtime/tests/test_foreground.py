from __future__ import annotations

import pytest
from y5n.base.flow.dsl import background, foreground, receive
from y5n.base.flow.primitives import AwaitEvent, Outcome, Stop, Suspend


@pytest.mark.asyncio
async def test_foreground_sets_focus(harness):
    """foreground() macht den Flow zum Foreground-Flow der Session."""

    async def handler(ctx):
        yield foreground()
        yield Outcome(control=Suspend())

    flow = await harness.start(handler)

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Suspend)
    assert harness.session.foreground_flow is flow

    await flow.control.resume(flow, harness.session)
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)
    assert harness.session.foreground_flow is None


@pytest.mark.asyncio
async def test_background_clears_focus(harness):
    """background() entfernt den Flow aus dem Foreground-Status."""

    async def handler(ctx):
        yield foreground()
        yield background()
        yield Outcome(control=Suspend())

    flow = await harness.start(handler)

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Suspend)
    assert harness.session.foreground_flow is None

    await flow.control.resume(flow, harness.session)
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)


@pytest.mark.asyncio
async def test_foreground_receives_user_input(harness):
    """Nur der Foreground-Flow empfängt User Input.
    Ein Background-Flow, der auf receive() wartet, bleibt blockiert."""

    received: list[str] = []

    async def fg_handler(ctx):
        yield foreground()
        event = yield receive()
        received.append(event.payload)
        yield Outcome()

    async def bg_handler(ctx):
        event = yield receive()
        received.append(event.payload)
        yield Outcome()

    fg = await harness.start(fg_handler)
    bg = await harness.start(bg_handler)

    # Beide blocken auf USER_INPUT
    await harness.run_until_blocked(fg)
    await harness.run_until_blocked(bg)

    # Simuliert Runner: Input nur an Foreground-Flow
    harness.send_user_input(fg, "hello")

    outcome = await harness.run_until_blocked(fg)
    assert isinstance(outcome.control, Stop)

    assert received == ["hello"]
    assert not bg.control.is_runnable(bg, harness.session)


@pytest.mark.asyncio
async def test_foreground_switch(harness):
    """foreground() wechselt den Fokus zum zuletzt aufgerufenen Flow."""

    received: list[str] = []

    async def handler_a(ctx):
        yield foreground()
        event = yield receive()
        received.append(f"a:{event.payload}")
        yield Outcome()

    async def handler_b(ctx):
        yield foreground()
        event = yield receive()
        received.append(f"b:{event.payload}")
        yield Outcome()

    flow_a = await harness.start(handler_a)
    outcome = await harness.run_until_blocked(flow_a)
    assert isinstance(outcome.control, AwaitEvent)
    assert harness.session.foreground_flow is flow_a

    flow_b = await harness.start(handler_b)
    outcome = await harness.run_until_blocked(flow_b)
    assert isinstance(outcome.control, AwaitEvent)
    assert harness.session.foreground_flow is flow_b

    # User Input geht an flow_b (neuer Foreground)
    harness.send_user_input(flow_b, "hello")

    outcome = await harness.run_until_blocked(flow_b)
    assert isinstance(outcome.control, Stop)
    assert received == ["b:hello"]

    # flow_a ist immer noch blockiert — hat nichts bekommen
    assert not flow_a.control.is_runnable(flow_a, harness.session)


@pytest.mark.asyncio
async def test_error_kills_foreground(harness):
    """Foreground-Flow wirft Exception → Scheduler killt den Flow und räumt Fokus.

    scheduler.py:204-207 fängt die Exception, ruft
    session.del_flow(session.foreground_flow) auf, was den Fokus löscht.
    """

    async def handler(ctx):
        yield foreground()
        raise RuntimeError("boom")

    flow = await harness.start(handler)

    # Schritt: foreground() → Foreground-Effekt angewandt,
    # dann im zweiten Loop-Durchlauf: Generator wirft RuntimeError
    with pytest.raises(RuntimeError, match="boom"):
        await harness.run_until_blocked(flow)

    # Foreground war gesetzt (vor dem Crash)
    assert harness.session.foreground_flow is flow

    # Simuliere scheduler.run() cleanup (scheduler.py:205-206)
    if harness.session.foreground_flow:
        harness.session.del_flow(harness.session.foreground_flow)

    assert harness.session.foreground_flow is None
    assert harness.session.get_flow(flow.id) is None
