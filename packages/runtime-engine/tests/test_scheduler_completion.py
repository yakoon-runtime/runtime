"""Scheduler-owned Flow completion observation (Slice 2A).

A generic primitive lets the caller that scheduled a Flow await that
exact Flow's normal Stop — independent of out_channel, output routing,
or any feature. One waiter per Flow; forcible removal (job stop) is
out of scope and leaves the waiter pending.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest
from support.flow import make_flow
from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.primitives import AwaitEvent, Pulse, Stop
from y5n.runtime.engine.machine.scheduler import Scheduler
from y5n.runtime.engine.nodes import Node


def _make_scheduler() -> tuple[Scheduler, dict]:
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
    return scheduler, calls


def _stop_flow(session, *, out_channel: str | None = None):
    """A flow whose next step is its normal Stop."""
    flow = make_flow(_single_step, session=session, payload="cmd")
    if out_channel:
        flow.out_channel = out_channel
    return flow


async def _single_step():
    yield Pulse(control=Stop())


def _parked(session, *, channel="never"):
    """A flow parked on AwaitEvent that never receives mail."""
    flow = make_flow(_single_step, session=session, payload="cmd")
    flow.control = AwaitEvent(channel=channel, scope=Scope.SESSION)
    return flow


async def _run_briefly(scheduler):
    scheduler._running = True
    task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0.02)
    scheduler._running = False
    scheduler._event.set()
    await task


# ----------------------------------------
# 1 + 2. waiter pending while Flow is active / parked
# ----------------------------------------


async def test_waiter_stays_pending_while_flow_is_active(session):
    scheduler, _ = _make_scheduler()
    flow = make_flow(_single_step, session=session, payload="cmd")
    fut = scheduler.when_complete(flow, session)
    assert not fut.done()

    scheduler.schedule_flow(flow, session)
    await _run_briefly(scheduler)

    # The flow stepped but never reached Stop (its step is scripted to
    # keep it alive) — the waiter must still be pending.
    assert not fut.done()
    assert session.get_flow(flow.id) is not None


async def test_parked_await_event_flow_does_not_complete_the_waiter(session):
    scheduler, _ = _make_scheduler()
    flow = _parked(session)
    fut = scheduler.when_complete(flow, session)

    scheduler.schedule_flow(flow, session)
    await _run_briefly(scheduler)

    assert not fut.done()
    assert session.get_flow(flow.id) is not None


# ----------------------------------------
# 3. normal Stop completes the waiter exactly once
# ----------------------------------------


async def test_normal_stop_completes_waiter_exactly_once(session):
    scheduler, calls = _make_scheduler()
    flow = _stop_flow(session)
    fut = scheduler.when_complete(flow, session)

    await scheduler._handle_pulse(session, flow, Pulse(control=Stop()))

    assert fut.done()
    assert fut.result() is None
    assert calls["flow_complete"].await_count == 1
    assert scheduler._completions == {}


# ----------------------------------------
# 4. multiple independent Flows wake only their own waiter
# ----------------------------------------


async def test_flows_wake_only_their_own_waiter(session):
    scheduler, _ = _make_scheduler()

    flow_a = _stop_flow(session)
    flow_b = _parked(session)
    fut_a = scheduler.when_complete(flow_a, session)
    fut_b = scheduler.when_complete(flow_b, session)

    await scheduler._handle_pulse(session, flow_a, Pulse(control=Stop()))

    assert fut_a.done()
    assert not fut_b.done()

    await scheduler._handle_pulse(session, flow_b, Pulse(control=Stop()))

    assert fut_b.done()
    assert scheduler._completions == {}


# ----------------------------------------
# 5. Flow without a waiter behaves exactly as before
# ----------------------------------------


async def test_flow_without_waiter_is_unaffected(session):
    scheduler, calls = _make_scheduler()
    flow = _stop_flow(session, out_channel="ch")

    await scheduler._handle_pulse(session, flow, Pulse(control=Stop()))

    event = session.pop_event(Scope.SESSION, "ch")
    assert event is not None
    assert calls["flow_complete"].await_count == 1
    assert scheduler._completions == {}
    assert session.get_flow(flow.id) is None


# ----------------------------------------
# 6. completion observation does not alter output/out_channel
# ----------------------------------------


async def test_completion_is_independent_of_out_channel(session):
    scheduler, _ = _make_scheduler()
    flow = _stop_flow(session, out_channel="ch")
    fut = scheduler.when_complete(flow, session)

    await scheduler._handle_pulse(session, flow, Pulse(control=Stop()))

    # the channel event is still pushed exactly as before …
    event = session.pop_event(Scope.SESSION, "ch")
    assert event is not None
    # … and the waiter resolves regardless of the channel
    assert fut.done()

    # a waiter on a flow without any channel produces no output event
    flow_plain = _stop_flow(session)
    fut_plain = scheduler.when_complete(flow_plain, session)
    await scheduler._handle_pulse(session, flow_plain, Pulse(control=Stop()))
    assert fut_plain.done()
    assert session.pop_event(Scope.SESSION, "ch") is None


# ----------------------------------------
# 7. no stale registry entry
# ----------------------------------------


async def test_no_stale_registry_entry_after_completion(session):
    scheduler, _ = _make_scheduler()
    flow = _stop_flow(session)
    fut = scheduler.when_complete(flow, session)

    await scheduler._handle_pulse(session, flow, Pulse(control=Stop()))

    assert fut.done()
    assert scheduler._completions == {}


# ----------------------------------------
# contract: single waiter, active Flow required
# ----------------------------------------


async def test_second_waiter_for_the_same_flow_is_rejected(session):
    scheduler, _ = _make_scheduler()
    flow = _stop_flow(session)
    scheduler.when_complete(flow, session)

    with pytest.raises(ValueError, match="already has a completion waiter"):
        scheduler.when_complete(flow, session)


async def test_waiter_for_inactive_flow_is_rejected(session):
    scheduler, _ = _make_scheduler()
    flow = _stop_flow(session)
    await scheduler._handle_pulse(session, flow, Pulse(control=Stop()))

    with pytest.raises(ValueError, match="not active"):
        scheduler.when_complete(flow, session)


# ----------------------------------------
# end-to-end through the run loop: register → schedule → complete
# ----------------------------------------


async def test_run_loop_completes_the_waiter(session):
    scheduler, _ = _make_scheduler()
    flow = _stop_flow(session)
    fut = scheduler.when_complete(flow, session)

    scheduler.on_step_flow = AsyncMock(return_value=Pulse(control=Stop()))
    scheduler.schedule_flow(flow, session)
    await _run_briefly(scheduler)

    assert fut.done()
    assert fut.result() is None
    assert scheduler._completions == {}
    assert session.get_flow(flow.id) is None
