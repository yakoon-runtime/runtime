from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.ui import View


class Control:
    pass


class YieldToScheduler(Control):
    pass


class Stop(Control):
    """Terminate the flow."""

    pass


class WaitForInput(Control):
    pass


# ------------------------------------------------------------
# Input Handling
# ------------------------------------------------------------


class AwaitInput(Control):
    """Pause execution and request user input."""

    def __init__(self, view: View | None, *, silent: bool = False):
        self.view = view
        self.silent = silent


# ------------------------------------------------------------
# Time Control
# ------------------------------------------------------------


class Sleep(Control):
    """Engine pauses for a duration."""

    def __init__(self, seconds: int):
        self.seconds = seconds


class SleepUntil(Control):
    """Engine pauses until timestamp."""

    def __init__(self, timestamp: float):
        self.timestamp = timestamp


BLOCKING_STEPS = (
    AwaitInput,
    WaitForInput,
    Sleep,
    SleepUntil,
    Stop,
)
