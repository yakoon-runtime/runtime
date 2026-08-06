from __future__ import annotations

import pytest
from y5n.runtime.api.flow.dsl import background, foreground, receive
from y5n.runtime.api.flow.primitives import AwaitEvent, Pulse, Stop, Suspend


@pytest.mark.asyncio
async def test_foreground_sets_focus(harness):
    """foreground() macht den Flow zum Foreground-Flow der Session."""

    async def handler():
        yield foreground()
        yield Pulse(control=Suspend())

    flow = await harness.start(handler)

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Suspend)
    assert harness.session.foreground_flow is flow

    await flow.control.resume(flow, harness.session)
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    assert harness.session.foreground_flow is None


@pytest.mark.asyncio
async def test_background_clears_focus(harness):
    """background() entfernt den Flow aus dem Foreground-Status."""

    async def handler():
        yield foreground()
        yield background()
        yield Pulse(control=Suspend())

    flow = await harness.start(handler)

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Suspend)
    assert harness.session.foreground_flow is None

    await flow.control.resume(flow, harness.session)
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)


@pytest.mark.asyncio
async def test_foreground_receives_user_input(harness):
    """Nur der Foreground-Flow empfängt User Input.
    Ein Background-Flow, der auf receive() wartet, bleibt blockiert."""

    received: list[str] = []

    async def fg_handler():
        yield foreground()
        event = yield receive()
        received.append(event.payload)
        yield Pulse()

    async def bg_handler():
        event = yield receive()
        received.append(event.payload)
        yield Pulse()

    fg = await harness.start(fg_handler)
    bg = await harness.start(bg_handler)

    # Beide blocken auf USER_INPUT
    await harness.run_until_blocked(fg)
    await harness.run_until_blocked(bg)

    # Simuliert Runner: Input nur an Foreground-Flow
    harness.send_user_input(fg, "hello")

    pulse = await harness.run_until_blocked(fg)
    assert isinstance(pulse.control, Stop)

    assert received == ["hello"]
    assert not bg.control.is_runnable(bg, harness.session)


@pytest.mark.asyncio
async def test_foreground_switch(harness):
    """foreground() wechselt den Fokus zum zuletzt aufgerufenen Flow."""

    received: list[str] = []

    async def handler_a():
        yield foreground()
        event = yield receive()
        received.append(f"a:{event.payload}")
        yield Pulse()

    async def handler_b():
        yield foreground()
        event = yield receive()
        received.append(f"b:{event.payload}")
        yield Pulse()

    flow_a = await harness.start(handler_a)
    pulse = await harness.run_until_blocked(flow_a)
    assert isinstance(pulse.control, AwaitEvent)
    assert harness.session.foreground_flow is flow_a

    flow_b = await harness.start(handler_b)
    pulse = await harness.run_until_blocked(flow_b)
    assert isinstance(pulse.control, AwaitEvent)
    assert harness.session.foreground_flow is flow_b

    # User Input geht an flow_b (neuer Foreground)
    harness.send_user_input(flow_b, "hello")

    pulse = await harness.run_until_blocked(flow_b)
    assert isinstance(pulse.control, Stop)
    assert received == ["b:hello"]

    # flow_a is still blocked — it got nothing
    assert not flow_a.control.is_runnable(flow_a, harness.session)


@pytest.mark.asyncio
async def test_error_routes_to_error_node(harness):
    """Exception im Generator → Flow wird auf /usr/bin/err geroutet.

    Der Fehler erzeugt eine neue Invocation; der bestehende Flow wird
    umgestellt (gleiche Flow-ID), der nächste Step führt den Error-Node
    aus (ADR: an error creates a new invocation).
    """

    async def handler():
        yield foreground()
        raise RuntimeError("boom")

    flow = await harness.start(handler)

    # Step 1: foreground() → Foreground-Effekt angewandt (control=None → None)
    assert await harness.engine.step_flow(flow, harness.session) is None

    # Step 2: Generator wirft RuntimeError → _route_error stellt den Flow um
    assert await harness.engine.step_flow(flow, harness.session) is None

    assert flow.error_depth == 1
    assert flow.node.key == "err"
    assert "error" in flow.invocation
    assert flow.invocation["error"]["type"] == "RuntimeError"
    assert harness.session.get_flow(flow.id) is flow
