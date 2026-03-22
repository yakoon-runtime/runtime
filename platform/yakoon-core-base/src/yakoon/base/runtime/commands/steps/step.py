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

    async def run(self, session, request) -> StepOutcome:
        raise NotImplementedError

    async def resume(self, session, data):
        return Next()


class ActiveStep(Step):

    async def resume(self, session, data):
        raise NotImplementedError

    def reject(self, field: str, message: str) -> AwaitInput:
        raise NotImplementedError


class PassiveStep(Step):
    pass


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


class Show(PassiveStep):

    def __init__(self, view: View):
        self.view = view

    async def run(self, session, request):
        await session.emit(self.view)
        return Next()


# ------------------------------------------------------------
# Ask
# ------------------------------------------------------------


class Ask(ActiveStep):

    def __init__(self, view: View, policy_service):
        self.view = view
        self.policy = policy_service

    # --------------------------------------------------------
    # Run
    # --------------------------------------------------------

    async def run(self, session, request) -> StepOutcome:
        # await session.emit(self.view)
        return AwaitInput(self.view)

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def reject(self, field: str, message: str) -> AwaitInput:
        view = self._apply_field_error(field, message)
        return AwaitInput(view)

    # --------------------------------------------------------
    # Resume
    # --------------------------------------------------------

    async def resume(self, session, raw_values: dict[str, Any]) -> StepOutcome:

        # ----------------------------------------------------
        # 1. Validation
        # ----------------------------------------------------

        validated: dict[str, Any] = {}
        errors: dict[str, list[FieldError]] = {}

        allowed_fields = {
            field.var
            for block in self.view.blocks
            for field in getattr(block, "fields", [])
        }

        unknown = set(raw_values.keys()) - allowed_fields
        if unknown:
            raise RuntimeError(f"Unknown fields: {unknown}")

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

                result = self.policy.validate(
                    policy_key=field.policy,
                    raw=raw,
                )

                if result.ok:
                    validated[field.var] = result.value
                    updated = updated.clear_errors()
                else:
                    ui_errors = [FieldError(message=e.message) for e in result.errors]
                    errors[field.var] = ui_errors
                    updated = updated.with_errors(ui_errors)

                new_fields.append(updated)

            new_blocks.append(replace(block, fields=new_fields))

        # ----------------------------------------------------
        # 2. Validation Fehler → Retry
        # ----------------------------------------------------

        if errors:
            self.view = self.view.with_body(new_blocks)
            return AwaitInput(self.view)

        # ----------------------------------------------------
        # 3. Erfolg
        # ----------------------------------------------------

        return InputResolved(validated)

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _with_header(self, *, role: str, title: str | None = None) -> View:

        header = self.view.header
        new_header = replace(header, role=role, title=title)  # or header.title,

        self.view = View(
            kind=self.view.kind,
            id=self.view.id,
            header=new_header,
            blocks=self.view.blocks,
        )

        return self.view

    def _apply_field_error(self, field_name: str, message: str) -> View:

        new_blocks = []

        for block in self.view.blocks:
            fields = getattr(block, "fields", None)

            if not fields:
                new_blocks.append(block)
                continue

            new_fields = []

            for f in fields:
                if f.var == field_name:
                    updated = f.with_errors([FieldError(message=message)])
                else:
                    updated = f

                new_fields.append(updated)

            new_blocks.append(replace(block, fields=new_fields))

        self.view = self.view.with_body(new_blocks)
        return self.view


# ------------------------------------------------------------
# Time-based
# ------------------------------------------------------------


class Form(ActiveStep):

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


class Delay(PassiveStep):
    def __init__(self, seconds: int):
        self.seconds = seconds

    async def run(self, session, request) -> StepOutcome:
        return Sleep(self.seconds)


class DelayUntil(PassiveStep):
    def __init__(self, timestamp: float):
        self.timestamp = timestamp

    async def run(self, session, request) -> StepOutcome:
        return SleepUntil(self.timestamp)
