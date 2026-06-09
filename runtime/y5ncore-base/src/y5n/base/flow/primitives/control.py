from __future__ import annotations

import time
from typing import TYPE_CHECKING

from y5n.base.flow.channel import Scope
from y5n.base.runtime import Event

if TYPE_CHECKING:
    from ..protocol import Flow


class Control:
    """Base class for controls.

    Controls determine what happens next in a flow's lifecycle.
    Subclasses implement is_runnable, on_enter, and on_wake.
    """

    blocking = False

    def is_runnable(self, flow, session) -> bool:
        return True

    async def on_enter(self, flow, scheduler, session):
        pass

    async def on_wake(self, flow, scheduler, session):
        scheduler.schedule_flow(flow, session)

    async def resume(self, flow, session):
        pass

    def label(self, flow) -> str:
        return self.__class__.__name__


class YieldToScheduler(Control):
    """Yield control back to the scheduler.

    The flow is ready to continue and will be picked up in the next cycle.
    """

    async def on_enter(self, flow, scheduler, session):
        scheduler.schedule_flow(flow, session)


class Stop(Control):
    """Terminate the flow and remove it from the session.

    This is the normal end-of-life for a flow (generator exhausted).
    """

    blocking = True

    async def on_enter(self, flow, scheduler, session):
        session.del_flow(flow)
        flow.scheduled = False


class Suspend(Control):
    """Suspend the flow indefinitely.

    The flow is blocked until resume() is called externally
    (e.g. by the job manager).
    """

    blocking = True

    def is_runnable(self, flow, session):
        return False

    async def resume(self, flow, session):
        flow.control = YieldToScheduler()


class Continue(Control):
    """Continue to the next command in the pipeline.

    Used internally when a pipeline (cmd | cmd | cmd) advances
    to the next stage.
    """

    blocking = False

    def __init__(self, data):
        self.data = data

    async def on_enter(self, flow, scheduler, session):

        if not flow.pipeline:
            return

        # 1. Fetch next command
        next_cmd = flow.pipeline[0]
        remaining = flow.pipeline[1:]

        # 2. Prepare event for next command
        event = Event(payload=next_cmd)

        # 3. Continue scheduling flow
        await scheduler.continue_flow(session, flow, event, remaining)


# ------------------------------------------------------------
# Event Handling
# ------------------------------------------------------------


class AwaitEvent(Control):
    """Block the flow until an event arrives on the specified channel.

    This is the primitive behind receive(). The scheduler checks
    *scope* and *channel* for mail; if found, the flow continues.
    """

    blocking = True

    def __init__(self, channel: str = "default", scope: Scope = Scope.FLOW):
        if scope == Scope.USER_INPUT and channel != "__user__":
            raise ValueError(
                f"USER_INPUT scope requires channel='__user__', got {channel!r}"
            )
        self.channel = channel
        self.scope = scope

    def label(self, flow):
        return "wait"

    def is_runnable(self, flow: Flow, session) -> bool:
        return session.has_mail(self.scope, self.channel, flow=flow)

    async def on_enter(self, flow, scheduler, session):
        if session.has_mail(self.scope, self.channel, flow=flow):
            scheduler.schedule_flow(flow, session)


# ------------------------------------------------------------
# Time Control
# ------------------------------------------------------------


class Sleep(Control):
    """Block the flow for a relative duration.

    The scheduler places the flow on a sleep heap and wakes it
    after *wake_at* (absolute timestamp).  Users call delay(seconds).
    """

    blocking = True

    def __init__(self, wake_at: float):
        self.wake_at = wake_at

    def is_runnable(self, flow, session):
        return False

    async def on_enter(self, flow, scheduler, session):
        scheduler.schedule_sleep(flow, session, self.wake_at)

    async def on_wake(self, flow, scheduler, session):
        flow.control = YieldToScheduler()
        scheduler.schedule_flow(flow, session)

    def label(self, flow) -> str:
        remaining = max(0, int(self.wake_at - time.time()))
        return f"sleep ({remaining}s)"

    @classmethod
    def for_duration(cls, seconds: float) -> Sleep:
        if seconds < 0:
            raise ValueError("Sleep duration must be >= 0")

        return cls(time.time() + seconds)


class SleepUntil(Control):
    """Block the flow until an absolute timestamp.

    Like Sleep but takes a fixed wall-clock time instead of a duration.
    Users call delay_until(timestamp).
    """

    blocking = True

    def __init__(self, timestamp: float):
        self.timestamp = timestamp

    def is_runnable(self, flow, session):
        return False

    async def on_enter(self, flow, scheduler, session):
        scheduler.schedule_sleep(flow, session, self.timestamp)

    async def on_wake(self, flow, scheduler, session):
        flow.control = YieldToScheduler()
        scheduler.schedule_flow(flow, session)

    def label(self, flow) -> str:
        return "sleep"

    @classmethod
    def until(cls, timestamp: float) -> SleepUntil:
        return cls(timestamp)
