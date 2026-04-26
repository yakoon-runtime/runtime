from __future__ import annotations

import time
from typing import TYPE_CHECKING

from yakoon.base.runtime.input import InputEvent

if TYPE_CHECKING:
    pass


class Control:
    blocking = False

    def is_runnable(self, flow) -> bool:
        return True

    async def on_enter(self, flow, scheduler, session):
        pass

    async def on_wake(self, flow, scheduler, session):
        scheduler.schedule_flow(flow, session)

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
        event = InputEvent(
            command=next_cmd, tokens=[], payload=self.data  # später sauber lösen
        )

        # 3. Flow weiter schedulen
        await scheduler.continue_flow(session, flow, event, remaining)


# ------------------------------------------------------------
# Event Handling
# ------------------------------------------------------------


class AwaitEvent(Control):

    blocking = True

    def __init__(self, channel: str = "default"):
        self.channel = channel

    def label(self, flow):
        return "wait"

    def is_runnable(self, flow):
        return flow.has_mail(self.channel)

    async def on_enter(self, flow, scheduler, session):
        # IMPORTANT:
        # If an event is already present, we must explicitly reschedule the flow.
        #
        # This is required for intra-tick scenarios like:
        #   yield send(...)
        #   data = yield receive(...)
        #
        # In this case, no external scheduler trigger exists.
        # Without this reschedule, the flow would remain blocked
        # even though the event is already available.
        #
        # Note:
        # This does NOT violate the "one step per tick" rule.
        # It only ensures the next tick is scheduled.
        if flow.has_mail(self.channel):
            scheduler.schedule_flow(flow, session)


# ------------------------------------------------------------
# Time Control
# ------------------------------------------------------------


class Sleep(Control):
    blocking = True

    def __init__(self, wake_at: float):
        self.wake_at = wake_at

    def is_runnable(self, flow):
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

    def is_runnable(self, flow):
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
