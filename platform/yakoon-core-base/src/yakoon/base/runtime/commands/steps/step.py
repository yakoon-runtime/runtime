from __future__ import annotations

from dataclasses import replace
from typing import Any

from yakoon.base.ui import FieldError, View

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
    def __init__(self, view: View):
        self.view = view

    async def run(self, session, request):
        await session.emit(self.view)
        return Next()


# ------------------------------------------------------------
# Ask
# ------------------------------------------------------------


class Ask(Step):
    def __init__(self, view: View, policy_service):
        self.view = view
        self.policy = policy_service

    async def run(self, session, request) -> StepOutcome:
        return AwaitInput(self.view)

    async def resume(self, session, raw_values: dict[str, Any]) -> StepOutcome:

        validated: dict[str, Any] = {}
        errors: dict[str, list[FieldError]] = {}

        # ------------------------
        # Validation vorbereiten
        # ------------------------

        allowed_fields = {
            field.var
            for block in self.view.blocks
            for field in getattr(block, "fields", [])
        }

        unknown = set(raw_values.keys()) - allowed_fields
        if unknown:
            raise RuntimeError(f"Unknown fields: {unknown}")

        # ------------------------
        # Blocks neu aufbauen
        # ------------------------

        new_blocks = []

        for block in self.view.blocks:

            fields = getattr(block, "fields", None)

            if not fields:
                new_blocks.append(block)
                continue

            new_fields = []

            for field in fields:

                raw = raw_values.get(field.var)

                updated = field.with_value(raw)

                # nur validieren, wenn kein unknown error
                if not errors:

                    result = self.policy.validate(
                        policy_key=field.policy,
                        raw=raw,
                    )

                    if result.ok:
                        validated[field.var] = result.value
                        updated = updated.clear_errors()
                    else:
                        ui_errors = [
                            FieldError(message=e.message) for e in result.errors
                        ]

                        errors[field.var] = ui_errors
                        updated = updated.with_errors(ui_errors)

                new_fields.append(updated)

            # neuen Block erzeugen (immutable!)
            new_block = replace(block, fields=new_fields)

            new_blocks.append(new_block)

        # ------------------------
        # Fehler → neuer View
        # ------------------------

        if errors:
            new_view = self.view.with_body(new_blocks)

            return AwaitInput(new_view)

        # ------------------------
        # Erfolg
        # ------------------------

        return InputResolved(validated)


# ------------------------------------------------------------
# Time-based
# ------------------------------------------------------------


class Form(Step):

    def __init__(self, views: list[View], policy_service):
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
            return AwaitInput(view)

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
