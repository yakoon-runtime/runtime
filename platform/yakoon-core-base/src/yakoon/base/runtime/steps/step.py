from __future__ import annotations

import time
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from yakoon.base.capabilities.interaction.port import PolicyService
from yakoon.base.runtime.input import InputEvent
from yakoon.base.runtime.steps import Emit, SetFocus
from yakoon.base.ui import FieldError, View
from yakoon.base.ui.view import ViewHeader

if TYPE_CHECKING:
    from yakoon.base.runtime.flow import Flow

from .context import StepContext
from .controls import AwaitInput, Sleep, SleepUntil
from .outcome import Outcome

# ============================================================
# Step Base
# ============================================================


class Step:
    async def run(self, flow: Flow, context: StepContext) -> Outcome:
        raise NotImplementedError


class InputStep(Step):
    async def resume(
        self, flow: Flow, event: InputEvent, context: StepContext
    ) -> Outcome:
        raise NotImplementedError

    def reject(self, field: str, message: str) -> Outcome:
        raise NotImplementedError


class PassiveStep(Step):
    pass


# ============================================================
# Concrete Steps
# ============================================================


# ------------------------------------------------------------
# Show
# ------------------------------------------------------------


class Show(PassiveStep):

    def __init__(self, view: View):
        self.view = view

    async def run(self, flow: Flow, context: StepContext) -> Outcome:
        return Outcome(
            effects=[
                Emit(self.view),
            ]
        )


# ------------------------------------------------------------
# Ask
# ------------------------------------------------------------


class Ask(InputStep):

    def __init__(self, view: View):
        header = replace(
            view.header or ViewHeader(),
            expects_input=True,
        )
        self.view = replace(view, header=header)

    async def run(self, flow: Flow, context: StepContext) -> Outcome:
        return Outcome(
            control=AwaitInput(self.view),
            effects=[
                SetFocus(flow.id),
                Emit(self.view),
            ],
        )

    async def resume(
        self, flow: Flow, event: InputEvent, context: StepContext
    ) -> Outcome:

        policy = context.get(PolicyService)

        validated: dict[str, Any] = {}
        errors: dict[str, list[FieldError]] = {}

        raw_values = event.to_values()

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

                result = policy.validate(
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

        if errors:
            self.view = self.view.with_body(new_blocks)
            return Outcome(
                control=AwaitInput(self.view),
                effects=[Emit(self.view)],
            )

        return Outcome(value=InputEvent(validated))


# ------------------------------------------------------------
# Receive
# ------------------------------------------------------------


class Receive(PassiveStep):

    def __init__(self, default: InputEvent | None = None, wait: bool = False):
        self.default = default
        self.wait = wait

    async def run(self, flow: Flow, context: StepContext) -> Outcome:

        event = flow.pop_event()
        if event:
            return Outcome(value=event)

        if self.wait:
            return Outcome(control=AwaitInput(None))

        return Outcome(value=self.default)


# ------------------------------------------------------------
# Delay
# ------------------------------------------------------------


class Delay(PassiveStep):

    def __init__(self, seconds: int):
        self.seconds = seconds

    async def run(self, flow: Flow, context: StepContext) -> Outcome:
        return Outcome(control=Sleep(time.time() + self.seconds))


class DelayUntil(PassiveStep):

    def __init__(self, timestamp: float):
        self.timestamp = timestamp

    async def run(self, flow: Flow, context: StepContext) -> Outcome:
        return Outcome(control=SleepUntil(self.timestamp))
