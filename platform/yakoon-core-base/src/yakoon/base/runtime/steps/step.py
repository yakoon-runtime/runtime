from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from yakoon.base.host.events import InputEvent
from yakoon.base.runtime.steps import Emit, SetFocus
from yakoon.base.ui import FieldError, View

if TYPE_CHECKING:
    from yakoon.base.runtime.commands import Request
    from yakoon.base.runtime.flow import Flow
    from yakoon.base.runtime.sessions import Session


from .controls import (
    AwaitInput,
    Sleep,
    SleepUntil,
)
from .outcome import Outcome

# ============================================================
# Step Base
# ============================================================


class Step:

    async def run(self, session: Session, flow: Flow, request: Request) -> Outcome:
        raise NotImplementedError


class InputStep(Step):
    """Benötigt externes resume() (Ask, Form)"""

    async def resume(self, session: Session, flow: Flow, event: InputEvent) -> Outcome:
        raise NotImplementedError

    def reject(self, field: str, message: str) -> Outcome:
        raise NotImplementedError


class PassiveStep(Step):
    """Läuft vollständig innerhalb des Flows"""

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

    async def run(self, session: Session, flow: Flow, request: Request) -> Outcome:

        return Outcome(
            effects=[
                Emit(self.view),
            ]
        )


# ------------------------------------------------------------
# Ask
# ------------------------------------------------------------


class Ask(InputStep):

    def __init__(self, view: View, policy_service):
        self.view = view
        self.policy = policy_service

    async def run(self, session: Session, flow: Flow, request: Request) -> Outcome:

        return Outcome(
            control=AwaitInput(self.view),
            effects=[
                SetFocus(flow.id),
                Emit(self.view),
            ],
        )

    def reject(self, field: str, message: str) -> Outcome:
        view = self._apply_field_error(field, message)
        return Outcome(
            control=AwaitInput(view),
            effects=[
                Emit(view),
            ],
        )

    async def resume(self, session: Session, flow: Flow, event: InputEvent) -> Outcome:

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

        if errors:
            self.view = self.view.with_body(new_blocks)
            return Outcome(
                control=AwaitInput(self.view),
                effects=[
                    Emit(
                        self.view,
                    )
                ],
            )

        return Outcome(value=InputEvent(validated))

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
# Receive (NEW DESIGN)
# ------------------------------------------------------------


class Receive(PassiveStep):

    def __init__(self, default: InputEvent | None = None, wait: bool = False):
        self.default = default
        self.wait = wait

    async def run(self, session: Session, flow: Flow, request: Request) -> Outcome:

        event = flow.pop_event()
        if event:
            return Outcome(value=event)

        # blockieren
        if self.wait:
            return Outcome(control=AwaitInput(None))

        return Outcome(value=self.default)


# ------------------------------------------------------------
# Form
# ------------------------------------------------------------


class Form(InputStep):

    def __init__(self, view: View, policy_service):
        self.view = view
        self.policy = policy_service
        self.index = 0
        self.values = {}

    async def run(self, session: Session, flow: Flow, request: Request) -> Outcome:

        return Outcome(
            control=AwaitInput(self.view), effects=[Emit(self.view), SetFocus(flow.id)]
        )

    async def resume(self, session: Session, flow: Flow, event: InputEvent) -> Outcome:

        raw_values = event.to_values()

        validated = {}
        errors = {}

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
            return Outcome(
                control=AwaitInput(self.view),
                effects=[
                    Emit(
                        self.view,
                    )
                ],
            )

        return Outcome(value=InputEvent(validated))


# ------------------------------------------------------------
# Time-based
# ------------------------------------------------------------


class Delay(PassiveStep):
    def __init__(self, seconds: int):
        self.seconds = seconds

    async def run(self, session: Session, flow: Flow, request: Request) -> Outcome:
        return Outcome(control=Sleep(self.seconds))


class DelayUntil(PassiveStep):
    def __init__(self, timestamp: float):
        self.timestamp = timestamp

    async def run(self, session: Session, flow: Flow, request: Request) -> Outcome:
        return Outcome(control=SleepUntil(self.timestamp))
