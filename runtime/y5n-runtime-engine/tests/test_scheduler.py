"""Scheduler unit tests.

Covers the scheduling machinery directly:
  - ready-queue priority (system before user)
  - sleep heap + wake
  - pulse handling (Stop, blocked, unhandled)
  - waiting-channel rescheduling
  - dispatch/continue flow and error paths
  - the main run loop with budget exhaustion
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock

import pytest
from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.primitives import (
    AwaitEvent,
    Pulse,
    Sleep,
    Stop,
    YieldToScheduler,
)
from y5n.runtime.engine.nodes import Node
from y5n.runtime.api.runtime import Event
from y5n.runtime.engine.flow import Flow, FlowCursor
from y5n.runtime.engine.flow.types import FlowKind
from y5n.runtime.engine.machine.scheduler import Scheduler


def _make_scheduler(**overrides) -> tuple[Scheduler, dict]:
    calls: dict[str, AsyncMock] = {
        "dispatch": AsyncMock(return_value=None),
        "step": AsyncMock(return_value=None),
        "projection": AsyncMock(),
        "flow_complete": AsyncMock(),
    }
    scheduler = Scheduler(
        platform=Node(key="root"),
        on_dispatch=calls["dispatch"],
        on_step_flow=calls["step"],
        on_show_projection=calls["projection"],
        on_audit_warning=lambda **kw: None,
        on_flow_complete=calls["flow_complete"],
    )
    if "platform" in overrides:
        scheduler.platform = overrides["platform"]
    return scheduler, calls


def _make_flow(
    session,
    *,
    kind: FlowKind = FlowKind.USER,
    control=None,
    out_channel: str | None = None,
) -> Flow:
    flow = Flow(
        id=session.next_flow_id(),
        node=Node(key="test"),
        event=Event(payload="cmd"),
        cursor=FlowCursor("run"),
        kind=kind,
        control=control,
        out_channel=out_channel,
    )
    session.add_flow(flow)
    return flow


# ----------------------------------------
# READY QUEUE
# ----------------------------------------


def test_schedule_flow_sets_scheduled_flag(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session)

    scheduler.schedule_flow(flow, session)

    assert flow.scheduled is True
    assert (session, flow) in scheduler._ready_user


def test_schedule_flow_is_idempotent(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session)

    scheduler.schedule_flow(flow, session)
    scheduler.schedule_flow(flow, session)

    assert len(scheduler._ready_user) == 1


def test_system_flow_uses_priority_queue(session):
    scheduler, _ = _make_scheduler()
    user = _make_flow(session, kind=FlowKind.USER)
    system = _make_flow(session, kind=FlowKind.SYSTEM)

    scheduler.schedule_flow(user, session)
    scheduler.schedule_flow(system, session)

    popped = scheduler._ready_system.popleft()
    assert popped[1] is system


# ----------------------------------------
# SLEEP HEAP
# ----------------------------------------


def test_schedule_sleep_places_flow_on_heap(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session)

    scheduler.schedule_sleep(flow, session, wake_at=100.0)

    assert flow.wake_at == 100.0
    assert scheduler._sleeping[0][1] is session


async def test_wake_sleeping_wakes_due_flow(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session, control=Sleep(wake_at=time.time() - 1))
    scheduler.schedule_sleep(flow, session, wake_at=time.time() - 1)

    await scheduler._wake_sleeping()

    assert isinstance(flow.control, YieldToScheduler)
    assert flow.scheduled is True


async def test_wake_sleeping_ignores_future_flow(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session)
    scheduler.schedule_sleep(flow, session, wake_at=time.time() + 60)

    await scheduler._wake_sleeping()

    assert scheduler._sleeping  # still waiting


# ----------------------------------------
# PULSE HANDLING
# ----------------------------------------


async def test_handle_pulse_none_control_is_noop(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session)

    await scheduler._handle_pulse(session, flow, Pulse(control=None))

    assert flow.control is None


async def test_handle_pulse_stop_removes_flow(session):
    scheduler, calls = _make_scheduler()
    flow = _make_flow(session, control=Stop())

    await scheduler._handle_pulse(session, flow, Pulse(control=Stop()))

    assert session.get_flow(flow.id) is None
    calls["flow_complete"].assert_awaited_once_with(flow, session)


async def test_handle_pulse_stop_pushes_to_out_channel(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session, control=Stop(), out_channel="ch:1")

    await scheduler._handle_pulse(session, flow, Pulse(control=Stop()))

    assert session.get_flow(flow.id) is None


async def test_handle_pulse_unhandled_control_raises(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session)

    with pytest.raises(RuntimeError, match="Unhandled control"):
        await scheduler._handle_pulse(session, flow, Pulse(control=object()))  # type: ignore[arg-type]


# ----------------------------------------
# WAITING CHANNELS
# ----------------------------------------


def test_schedule_waiting_reschedules_blocked_flows(session):
    scheduler, _ = _make_scheduler()
    waiting = _make_flow(session, control=AwaitEvent(channel="ch:1"))
    other = _make_flow(session, control=AwaitEvent(channel="ch:2"))

    scheduler._schedule_waiting(session, "ch:1")

    assert waiting.scheduled is True
    assert other.scheduled is False


# ----------------------------------------
# RESUME / REFRESH
# ----------------------------------------


def test_refresh_resumed_flows_reschedules_yielders(session):
    scheduler, _ = _make_scheduler()
    yielded = _make_flow(session, control=YieldToScheduler())
    blocked = _make_flow(session, control=AwaitEvent(channel="ch"))

    scheduler._refresh_resumed_flows(session)

    assert yielded.scheduled is True
    assert blocked.scheduled is False


# ----------------------------------------
# DISPATCH / CONTINUE
# ----------------------------------------


async def test_continue_flow_schedules_both_flows(session):
    scheduler, _ = _make_scheduler()
    old = _make_flow(session)
    new = _make_flow(session)

    async def fake_dispatch(*, session, event):
        return new

    scheduler.on_dispatch = fake_dispatch

    await scheduler.continue_flow(session, old, Event(payload="x"), ["next"])

    assert new.pipeline == ["next"]
    assert old.scheduled is True
    assert new.scheduled is True


async def test_dispatch_error_propagates(session):
    scheduler, calls = _make_scheduler()

    async def boom(*, session, event):
        raise ValueError("boom")

    scheduler.on_dispatch = boom

    # Ein echter Runtime-Fehler beim Dispatch ist kein Benutzer-Fehler:
    # der Scheduler behandelt ihn nicht, er propagiert.
    with pytest.raises(ValueError, match="boom"):
        await scheduler.dispatch(session, Event(payload="x"))

    calls["projection"].assert_not_awaited()


# ----------------------------------------
# ERROR PATH
# ----------------------------------------


async def test_step_error_propagates(session):
    scheduler, calls = _make_scheduler()

    async def boom(*, flow, session):
        raise ValueError("boom")

    scheduler.on_step_flow = boom
    flow = _make_flow(session)

    # drive one flow through the main loop
    scheduler.schedule_flow(flow, session)
    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()

    # Ein echter Runtime-Fehler beim Steppen ist kein Benutzer-Fehler:
    # der Scheduler behandelt ihn nicht, er propagiert.
    with pytest.raises(ValueError, match="boom"):
        await task

    calls["projection"].assert_not_awaited()


# ----------------------------------------
# MAIN LOOP
# ----------------------------------------


async def test_run_processes_flow_until_stop(session):
    scheduler, calls = _make_scheduler()
    flow = _make_flow(session)
    scheduler.schedule_flow(flow, session)

    async def step(*, flow, session):
        return Pulse(control=Stop())

    scheduler.on_step_flow = step

    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()
    await task

    assert session.get_flow(flow.id) is None


async def test_run_requeues_flow_when_step_budget_exhausted(session):
    scheduler, calls = _make_scheduler()
    flow = _make_flow(session)
    scheduler.schedule_flow(flow, session)

    step_count = 0

    async def step(*, flow, session):
        nonlocal step_count
        step_count += 1
        return None  # no pulse → continues stepping until budget

    scheduler.on_step_flow = step

    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()
    await task

    # Budget (MAX_STEPS_PER_FLOW) was reached → flow re-scheduled
    assert step_count >= scheduler.MAX_STEPS_PER_FLOW
    assert flow.scheduled is True


async def test_run_skips_flow_removed_from_session(session):
    scheduler, calls = _make_scheduler()
    flow = _make_flow(session)
    scheduler.schedule_flow(flow, session)
    session.del_flow(flow)

    stepper = AsyncMock(return_value=Pulse(control=Stop()))
    scheduler.on_step_flow = stepper

    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()
    await task

    stepper.assert_not_called()


async def test_run_gives_system_priority(session):
    scheduler, _ = _make_scheduler()
    order: list[str] = []
    user = _make_flow(session, kind=FlowKind.USER)
    system = _make_flow(session, kind=FlowKind.SYSTEM)
    scheduler.schedule_flow(user, session)
    scheduler.schedule_flow(system, session)

    async def step(*, flow, session):
        order.append(flow.id)
        return Pulse(control=Stop())

    scheduler.on_step_flow = step
    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()
    await task

    assert order == [system.id, user.id]


async def test_run_skips_blocked_flow(session):
    scheduler, calls = _make_scheduler()
    blocked = _make_flow(
        session, control=AwaitEvent(channel="never", scope=Scope.SESSION)
    )
    scheduler.schedule_flow(blocked, session)

    stepper = AsyncMock(return_value=None)
    scheduler.on_step_flow = stepper

    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()
    await task

    stepper.assert_not_called()


async def test_run_warns_at_iteration_limit(session, monkeypatch):
    scheduler, _ = _make_scheduler()
    warnings: list[tuple[str, object]] = []
    scheduler.on_audit_warning = lambda *, message, session: warnings.append(
        (message, session)
    )
    monkeypatch.setattr(Scheduler, "MAX_ITERATIONS", 2)

    for _ in range(5):
        flow = _make_flow(session)
        scheduler.schedule_flow(flow, session)

    async def step(*, flow, session):
        return Pulse(control=Stop())

    scheduler.on_step_flow = step
    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()
    await task

    assert any("iteration limit" in msg for msg, _ in warnings)


async def test_run_propagates_runtime_error(session):
    scheduler, calls = _make_scheduler()
    flow = _make_flow(session)
    session.set_foreground_flow(flow.id)
    scheduler.schedule_flow(flow, session)

    async def boom(*, flow, session):
        raise ValueError("boom")

    scheduler.on_step_flow = boom
    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()

    # Ein echter Runtime-Fehler ist kein Benutzer-Fehler: der Scheduler
    # behandelt ihn nicht, er propagiert.
    with pytest.raises(ValueError, match="boom"):
        await task

    calls["projection"].assert_not_awaited()


async def test_wake_sleeping_skips_flow_without_control(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session)
    scheduler.schedule_sleep(flow, session, wake_at=time.time() - 1)

    await scheduler._wake_sleeping()

    assert scheduler._sleeping == []


async def test_call_runtime_schedules_session_flows(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session)
    other = _make_flow(session)

    async def fake_dispatch(*, session, event):
        return flow

    scheduler.on_dispatch = fake_dispatch

    await scheduler.dispatch(session, Event(payload="x"))

    assert flow.scheduled is True
    assert other.scheduled is True


async def test_run_waits_for_sleeping_flow_timeout(session):
    scheduler, _ = _make_scheduler()
    flow = _make_flow(session, control=Sleep(wake_at=time.time() + 0.001))
    scheduler.schedule_sleep(flow, session, wake_at=time.time() + 0.001)

    stepped = AsyncMock(return_value=Pulse(control=Stop()))
    scheduler.on_step_flow = stepped

    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()
    await task

    # Timeout expired → the sleeping flow was woken and stepped
    stepped.assert_awaited()


async def test_run_enforces_flow_time_budget(session, monkeypatch):
    scheduler, _ = _make_scheduler()

    class FakeTime:
        def __init__(self) -> None:
            self.value = 0.0

        def now(self) -> float:
            self.value += 0.005
            return self.value

    fake = FakeTime()
    monkeypatch.setattr("y5n.runtime.engine.machine.scheduler.time.time", fake.now)

    flow = _make_flow(session)
    scheduler.schedule_flow(flow, session)

    async def step(*, flow, session):
        return None  # no pulse → keeps stepping until budget

    scheduler.on_step_flow = step
    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()
    await task

    # MAX_TIME_PER_FLOW (0.002s) was exceeded → flow re-scheduled
    assert flow.scheduled is True
