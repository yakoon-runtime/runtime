from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Control:
    blocking = False

    def is_runnable(self, flow) -> bool:
        return True

    def on_enter(self, flow, scheduler, session):
        pass

    def on_wake(self, flow, scheduler, session):
        scheduler.schedule_flow(flow, session)

    def label(self, flow) -> str:
        return self.__class__.__name__


class YieldToScheduler(Control):

    def on_enter(self, flow, scheduler, session):
        scheduler.schedule_flow(flow, session)


class Stop(Control):
    blocking = True

    def on_enter(self, flow, scheduler, session):
        session.del_flow(flow)
        flow.scheduled = False


# ------------------------------------------------------------
# Input Handling
# ------------------------------------------------------------


class AwaitInput(Control):
    blocking = True

    def __init__(self, view=None):
        self.view = view

    def is_runnable(self, flow):
        return bool(flow.input_queue)

    def label(self, flow) -> str:
        return "input"


# ------------------------------------------------------------
# Time Control
# ------------------------------------------------------------


class Sleep(Control):
    blocking = True

    def __init__(self, wake_at: float):
        self.wake_at = wake_at

    def is_runnable(self, flow):
        return False

    def on_enter(self, flow, scheduler, session):
        scheduler.schedule_sleep(flow, session, self.wake_at)

    def on_wake(self, flow, scheduler, session):
        flow.control = YieldToScheduler()
        scheduler.schedule_flow(flow, session)

    def label(self, flow) -> str:
        remaining = max(0, int(self.wake_at - time.time()))
        return f"sleep ({remaining}s)"


class SleepUntil(Control):
    blocking = True

    def __init__(self, timestamp: float):
        self.timestamp = timestamp

    def is_runnable(self, flow):
        return False

    def on_enter(self, flow, scheduler, session):
        scheduler.schedule_sleep(flow, session, self.timestamp)

    def on_wake(self, flow, scheduler, session):
        flow.control = YieldToScheduler()
        scheduler.schedule_flow(flow, session)

    def label(self, flow) -> str:
        return "sleep"
