from __future__ import annotations

from typing import Any

# ============================================================
# Step Outcomes (Engine Control)
# ============================================================


class StepOutcome:
    """Defines how the engine proceeds after a step."""

    pass


# ------------------------------------------------------------
# Flow Control
# ------------------------------------------------------------


class Next(StepOutcome):
    """Continue immediately with the next step."""

    pass


class Stop(StepOutcome):
    """Terminate the flow."""

    pass


# ------------------------------------------------------------
# Input Handling
# ------------------------------------------------------------


class AwaitInput(StepOutcome):
    """Pause execution and request user input."""

    def __init__(
        self,
        block,
        *,
        errors: dict[str, Any] | None = None,
        values: dict[str, Any] | None = None,
    ):
        self.block = block
        self.errors = errors or {}
        self.values = values or {}


class InputResolved(StepOutcome):
    """Validated input ready to be fed back into the flow."""

    def __init__(self, data: dict[str, Any]):
        self.data = data


# ------------------------------------------------------------
# Time Control
# ------------------------------------------------------------


class Sleep(StepOutcome):
    """Engine pauses for a duration."""

    def __init__(self, seconds: int):
        self.seconds = seconds


class SleepUntil(StepOutcome):
    """Engine pauses until timestamp."""

    def __init__(self, timestamp: float):
        self.timestamp = timestamp
