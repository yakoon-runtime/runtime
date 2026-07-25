from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.runtime import Event, InputContext
from y5n.runtime.api.runtime.input import Origin

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

    def on_activate(self):
        """Return the control state when the flow is activated.

        Override in subclasses that need to unblock or change
        state when the flow is brought to the foreground.
        """
        return self

    def label(self) -> str:
        return self.__class__.__name__


class YieldToScheduler(Control):
    """Yield control back to the scheduler.

    The flow is ready to continue and will be picked up in the next cycle.
    """

    async def on_enter(self, flow, scheduler, session):
        scheduler.schedule_flow(flow, session)


@dataclass(slots=True)
class Stop(Control):
    """Terminate the flow and remove it from the session.

    This is the normal end-of-life for a flow (generator exhausted).
    """

    blocking: ClassVar[bool] = True

    async def on_enter(self, flow, scheduler, session):
        session.del_flow(flow)
        flow.scheduled = False


@dataclass(slots=True)
class Suspend(Control):
    """Suspend the flow indefinitely.

    The flow is blocked until resume() is called externally
    (e.g. by the job manager).
    """

    blocking: ClassVar[bool] = True

    def is_runnable(self, flow, session):
        return False

    async def resume(self, flow, session):
        flow.control = YieldToScheduler()

    def on_activate(self):
        return YieldToScheduler()


@dataclass(slots=True)
class Continue(Control):
    """Continue to the next command in the pipeline.

    Pops the next entry from *flow.pipeline* (a command string or a
    pre-built ``Request``) and dispatches it as the next flow.
    """

    blocking: ClassVar[bool] = False

    async def on_enter(self, flow, scheduler, session):

        if not flow.pipeline:
            return

        next_cmd = flow.pipeline.pop(0)
        remaining = flow.pipeline[:]
        event = Event(
            payload=next_cmd,
            context=InputContext(origin=Origin.SCHEDULER),
        )
        await scheduler.continue_flow(session, flow, event, remaining)


# ------------------------------------------------------------
# Event Handling
# ------------------------------------------------------------


@dataclass(slots=True)
class AwaitEvent(Control):
    """Block the flow until an event arrives on the specified channel.

    This is the primitive behind receive(). The scheduler checks
    *scope* and *channel* for mail; if found, the flow continues.
    """

    channel: str = "default"
    scope: Scope = Scope.FLOW
    blocking: ClassVar[bool] = True

    def __post_init__(self):
        if self.scope == Scope.USER_INPUT and self.channel != "__user__":
            raise ValueError(
                f"USER_INPUT scope requires channel='__user__', got {self.channel!r}"
            )

    def label(self):
        return "wait"

    def is_runnable(self, flow: Flow, session) -> bool:
        return session.has_mail(self.scope, self.channel, flow=flow)

    async def on_enter(self, flow, scheduler, session):
        if session.has_mail(self.scope, self.channel, flow=flow):
            scheduler.schedule_flow(flow, session)


# ------------------------------------------------------------
# Time Control
# ------------------------------------------------------------


@dataclass(slots=True)
class Sleep(Control):
    """Block the flow for a relative duration.

    The scheduler places the flow on a sleep heap and wakes it
    after *wake_at* (absolute timestamp).  Users call delay(seconds).
    """

    wake_at: float = 0.0
    blocking: ClassVar[bool] = True

    def is_runnable(self, flow, session):
        return False

    async def on_enter(self, flow, scheduler, session):
        scheduler.schedule_sleep(flow, session, self.wake_at)

    async def on_wake(self, flow, scheduler, session):
        flow.control = YieldToScheduler()
        scheduler.schedule_flow(flow, session)

    def label(self) -> str:
        remaining = max(0, int(self.wake_at - time.time()))
        return f"sleep ({remaining}s)"

    @classmethod
    def for_duration(cls, seconds: float) -> Sleep:
        if seconds < 0:
            raise ValueError("Sleep duration must be >= 0")

        return cls(time.time() + seconds)


@dataclass(slots=True)
class SleepUntil(Control):
    """Block the flow until an absolute timestamp.

    Like Sleep but takes a fixed wall-clock time instead of a duration.
    Users call delay_until(timestamp).
    """

    timestamp: float = 0.0
    blocking: ClassVar[bool] = True

    def is_runnable(self, flow, session):
        return False

    async def on_enter(self, flow, scheduler, session):
        scheduler.schedule_sleep(flow, session, self.timestamp)

    async def on_wake(self, flow, scheduler, session):
        flow.control = YieldToScheduler()
        scheduler.schedule_flow(flow, session)

    def label(self) -> str:
        return "sleep"

    @classmethod
    def until(cls, timestamp: float) -> SleepUntil:
        return cls(timestamp)
