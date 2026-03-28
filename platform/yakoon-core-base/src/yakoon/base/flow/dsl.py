import time
from dataclasses import dataclass, replace
from typing import Any, TypeGuard

from yakoon.base.capabilities.interaction import PolicyService
from yakoon.base.capabilities.presenters import PresenterView
from yakoon.base.presentation import FieldError, View, ViewHeader, v_text
from yakoon.base.runtime.input import InputEvent
from yakoon.base.runtime.services import ServiceDirectory

from .primitives import AutoFocus, AwaitInput, Emit, Outcome, Sleep, SleepUntil


def show(view: View | PresenterView):
    if isinstance(view, View):
        return Outcome(effects=[Emit(view)])
    if _is_pv(view):
        return Outcome(effects=[Emit(view.view)])
    raise TypeError(f"show() expected View or PresenterView, got {type(view).__name__}")


def ask(
    view: View | PresenterView, *, policy: str | None = None, required: bool = False
):

    def update_header(view: View) -> View:
        header = replace(view.header or ViewHeader(), expects_input=True)
        return replace(view, header=header)

    if isinstance(view, View):
        view = update_header(view)
        return Outcome(effects=[AutoFocus(), Emit(view)], control=AwaitInput())
    elif _is_pv(view):
        view = update_header(view.view)
        return Outcome(effects=[AutoFocus(), Emit(view)], control=AwaitInput())

    raise TypeError(f"ask() expected View or PresenterView, got {type(view).__name__}")


def ask_until_valid(view: PresenterView, services: ServiceDirectory, *, on_error=None):

    while True:
        event = yield ask(view)

        result = validate(view, event, services)

        if not result.ok:
            if on_error:
                view = on_error(view, result)
            else:
                view = apply_errors(view, result.errors)
            continue

        return result.values


def receive(default: InputEvent | None = None, wait: bool = False):
    return Receive(default, wait)


def text(message: str):
    return show(v_text(message))


def delay(seconds: int):
    return Outcome(control=Sleep(time.time() + seconds))


def delay_until(timestamp: float):
    return Outcome(control=SleepUntil(timestamp))


# --------------------------------------------------------
# VALIDATION
# --------------------------------------------------------


@dataclass
class ValidationResult:
    ok: bool
    values: dict[str, Any]
    errors: dict[str, list[FieldError]]


def validate(
    view: PresenterView, event: InputEvent, services: ServiceDirectory
) -> ValidationResult:

    policy = services.get(PolicyService)

    values = {}
    errors = {}

    raw_values = event.to_values()

    for field in view.fields():
        if field.var is None:
            continue

        raw = raw_values.get(field.var)

        result = policy.validate(
            policy_key=field.policy,
            raw=raw,
        )

        if result.ok:
            values[field.var] = result.value
        else:
            errors[field.var] = [FieldError(message=e.message) for e in result.errors]

    return ValidationResult(
        ok=not errors,
        values=values,
        errors=errors,
    )


def apply_values(pv: PresenterView, values: dict[str, object]) -> PresenterView:

    view = pv.view
    new_blocks = []

    for block in view.blocks:
        fields = getattr(block, "fields", None)

        if not fields:
            new_blocks.append(block)
            continue

        updated_fields = []

        for f in fields:
            if f.var in values:
                updated_fields.append(f.with_value(values[f.var]).clear_errors())
            else:
                updated_fields.append(f)

        new_blocks.append(replace(block, fields=updated_fields))

    return pv.body_only(new_blocks)


def apply_errors(
    pv: PresenterView, errors: dict[str, list[FieldError]]
) -> PresenterView:

    view = pv.view
    new_blocks = []

    for block in view.blocks:
        fields = getattr(block, "fields", None)

        if not fields:
            new_blocks.append(block)
            continue

        updated_fields = []

        for f in fields:
            if f.var in errors:
                updated_fields.append(f.with_errors(errors[f.var]))
            else:
                # wichtig: alte Fehler entfernen
                updated_fields.append(f.clear_errors())

        new_blocks.append(replace(block, fields=updated_fields))

    return pv.body_only(new_blocks)


# --------------------------------------------------------
# INTERNALS
# --------------------------------------------------------


def _is_pv(v: object) -> TypeGuard[PresenterView]:
    return hasattr(v, "view")
