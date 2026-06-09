from __future__ import annotations

import time
from typing import TYPE_CHECKING

from y5n.base.flow.channel import Scope
from y5n.base.runtime import Event

if TYPE_CHECKING:
    from y5n.base.flow.protocol import Flow


class Control:
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

    async def on_enter(self, flow, scheduler, session):
        scheduler.schedule_flow(flow, session)


class Stop(Control):
    blocking = True

    async def on_enter(self, flow, scheduler, session):
        session.del_flow(flow)
        flow.scheduled = False


class Suspend(Control):

    blocking = True

    def is_runnable(self, flow, session):
        return False

    async def resume(self, flow, session):
        flow.control = YieldToScheduler()


class Continue(Control):
    blocking = False

    def __init__(self, data):
        self.data = data

    async def on_enter(self, flow, scheduler, session):

        if not flow.pipeline:
            return

        # 1. nächsten Command holen
        next_cmd = flow.pipeline[0]
        remaining = flow.pipeline[1:]

        # 2. Event für nächsten Command vorbereiten
        event = Event(payload=next_cmd)

        # 3. Flow weiter schedulen
        await scheduler.continue_flow(session, flow, event, remaining)


# ------------------------------------------------------------
# Event Handling
# ------------------------------------------------------------


class AwaitEvent(Control):

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
