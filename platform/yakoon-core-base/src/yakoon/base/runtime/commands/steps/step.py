from __future__ import annotations

from typing import Any

from yakoon.base.ui.document import ViewSpec

from .outcome import (
    AwaitInput,
    InputResolved,
    Next,
    Sleep,
    SleepUntil,
    StepOutcome,
)

# ============================================================
# Step Base
# ============================================================


class Step:
    """A unit of execution within a command flow."""

    async def run(self, session, request) -> StepOutcome:
        raise NotImplementedError

    async def resume(self, session, data: Any) -> StepOutcome:
        return Next()


# ============================================================
# Concrete Steps
# ============================================================


# ------------------------------------------------------------
# Flow Control
# ------------------------------------------------------------


class Advance(Step):
    """Explicitly advance the flow."""

    async def run(self, session, request) -> StepOutcome:
        return Next()


# ------------------------------------------------------------
# Show
# ------------------------------------------------------------


class Show(Step):
    def __init__(self, block, *, stream: str | None = None):
        self.block = block
        self.stream = stream

    async def run(self, session, request) -> StepOutcome:
        view = ViewSpec("view", blocks=[self.block])
        await session.emit(view)
        return Next()


# ------------------------------------------------------------
# Ask
# ------------------------------------------------------------


class Ask(Step):
    def __init__(self, block, policy_service):
        self.block = block
        self.policy = policy_service

    async def run(self, session, request) -> StepOutcome:
        return AwaitInput(self.block)

    async def resume(self, session, raw_values: dict[str, Any]) -> StepOutcome:

        validated: dict[str, Any] = {}
        errors: dict[str, Any] = {}

        for field in self.block.fields:
            raw = raw_values.get(field.var)

            result = self.policy.validate(
                policy_key=field.policy,
                raw=raw,
            )

            if result.ok:
                validated[field.var] = result.value
            else:
                errors[field.var] = result.errors

        if errors:
            return AwaitInput(
                self.block,
                errors=errors,
                values=raw_values,
            )

        return InputResolved(validated)


# ------------------------------------------------------------
# Time-based
# ------------------------------------------------------------


class Delay(Step):
    def __init__(self, seconds: int):
        self.seconds = seconds

    async def run(self, session, request) -> StepOutcome:
        return Sleep(self.seconds)


class DelayUntil(Step):
    def __init__(self, timestamp: float):
        self.timestamp = timestamp

    async def run(self, session, request) -> StepOutcome:
        return SleepUntil(self.timestamp)
