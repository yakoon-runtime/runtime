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


class Show:
    def __init__(self, view: ViewSpec):
        self.view = view

    async def run(self, session, request):
        await session.emit(self.view)
        return Next()


# ------------------------------------------------------------
# Ask
# ------------------------------------------------------------


class Ask(Step):
    def __init__(self, view: ViewSpec, policy_service):
        self.view = view
        self.policy = policy_service

    async def run(self, session, request) -> StepOutcome:
        return AwaitInput(self.view)

    async def resume(self, session, raw_values: dict[str, Any]) -> StepOutcome:

        validated: dict[str, Any] = {}
        errors: dict[str, Any] = {}

        for block in self.view.blocks:
            fields = getattr(block, "fields", None)
            if not fields:
                continue

            for field in fields:
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
                self.view,
                errors=errors,
                values=raw_values,
            )

        return InputResolved(validated)


# ------------------------------------------------------------
# Time-based
# ------------------------------------------------------------


class Form(Step):

    def __init__(self, views: list[ViewSpec], policy_service):
        self.views = views
        self.policy = policy_service
        self.index = 0
        self.values = {}

    async def run(self, session, request) -> StepOutcome:
        return AwaitInput(self.views[self.index])

    async def resume(self, session, raw_values):

        view = self.views[self.index]

        validated = {}
        errors = {}

        for block in view.blocks:
            fields = getattr(block, "fields", None)
            if not fields:
                continue

            for field in fields:
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
                view,
                errors=errors,
                values=raw_values,
            )

        self.values.update(validated)
        self.index += 1

        if self.index >= len(self.views):
            return InputResolved(self.values)

        return AwaitInput(self.views[self.index])


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
