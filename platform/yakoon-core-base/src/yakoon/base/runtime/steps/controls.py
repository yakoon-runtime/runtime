from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Control:

    def label(self) -> str:
        return self.__class__.__name__


class YieldToScheduler(Control):
    pass


class Stop(Control):
    """Terminate the flow."""

    pass


# ------------------------------------------------------------
# Input Handling
# ------------------------------------------------------------


class AwaitInput(Control):

    def label(self):
        return "waiting for input"


# ------------------------------------------------------------
# Time Control
# ------------------------------------------------------------


class Sleep(Control):
    """Engine pauses for a duration."""

    def __init__(self, seconds: int):
        self.seconds = seconds

    def label(self):
        remaining = int(self.seconds - time.time())
        return f"sleeping ({remaining}s)"


class SleepUntil(Control):
    """Engine pauses until timestamp."""

    def __init__(self, timestamp: float):
        self.timestamp = timestamp

    def label(self):
        return "sleeping"


BLOCKING_STEPS = (
    AwaitInput,
    Sleep,
    SleepUntil,
    Stop,
)
