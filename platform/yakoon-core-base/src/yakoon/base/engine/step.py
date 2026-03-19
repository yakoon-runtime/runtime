from __future__ import annotations

from enum import IntEnum
from typing import Any

# ============================================================
# Flow State
# ============================================================


class FlowState(IntEnum):
    RUNNING = 1
    WAITING = 2
    FINISHED = 3


class TickResult:
    def __init__(self, state: FlowState, outcome: StepOutcome | None):
        self.state = state
        self.outcome = outcome


# ============================================================
# Step Base
# ============================================================


class Step:
    async def run(self, session, request):
        raise NotImplementedError

    async def resume(self, session, input):
        # Default: einfach durchreichen
        return input


# ============================================================
# Outcomes
# ============================================================


class StepOutcome:
    pass


class Continue(StepOutcome):
    pass


class FlowFinished(StepOutcome):
    pass


class InputRequired(StepOutcome):
    def __init__(
        self, block, *, errors: dict | None = None, values: dict | None = None
    ):
        self.block = block
        self.errors = errors or {}
        self.values = values or {}


# ============================================================
# Steps
# ============================================================


class NoOp(Step):
    async def run(self, session, request):
        return Continue()


# ------------------------------------------------------------
# Show (Block-Level)
# ------------------------------------------------------------


class Show(Step):
    def __init__(self, block, *, stream: str | None = None):
        self.block = block
        self.stream = stream

    async def run(self, session, request):
        await session.emit_block(self.block, stream=self.stream)
        return Continue()


# ------------------------------------------------------------
# Ask (Block-Level)
# ------------------------------------------------------------


class Ask(Step):

    def __init__(self, block, policy_service):
        self.block = block
        self.policy = policy_service

    async def run(self, session, request):
        return InputRequired(self.block)

    async def resume(self, session, raw_values: dict[str, Any]):

        validated: dict[str, Any] = {}
        errors: dict[str, Any] = {}

        for field in self.block.fields:

            raw = raw_values.get(field.var)

            res = self.policy.validate(
                policy_key=field.policy,
                raw=raw,
            )

            if res.ok:
                validated[field.var] = res.value
            else:
                errors[field.var] = res.errors

        if errors:
            return InputRequired(
                self.block,
                errors=errors,
                values=raw_values,
            )

        return validated


# ------------------------------------------------------------
# TIME BASED
# ------------------------------------------------------------


class SleepRequired(StepOutcome):
    def __init__(self, seconds: int):
        self.seconds = seconds


class SleepUntilRequired(StepOutcome):
    def __init__(self, timestamp: float):
        self.timestamp = timestamp


class Wait(Step):
    def __init__(self, seconds: int):
        self.seconds = seconds

    async def run(self, session, request):
        return SleepRequired(seconds=self.seconds)


class WaitUntil(Step):
    def __init__(self, timestamp: float):
        self.timestamp = timestamp

    async def run(self, session, request):
        return SleepUntilRequired(timestamp=self.timestamp)
