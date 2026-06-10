from __future__ import annotations

import pytest
from y5n.base.flow.dsl import background, foreground, receive
from y5n.base.flow.primitives import Outcome, Stop, Suspend, YieldToScheduler


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
