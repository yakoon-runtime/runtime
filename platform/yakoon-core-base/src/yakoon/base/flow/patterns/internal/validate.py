from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from yakoon.base.capabilities.interaction import PolicyService
from yakoon.base.capabilities.presenters import PresenterView
from yakoon.base.projection import FieldError
from yakoon.base.runtime.input import InputEvent
from yakoon.base.runtime.services import ServiceDirectory


@dataclass
class ValidationResult:
    ok: bool
    values: dict[str, Any]
    errors: dict[str, list[FieldError]]


# --------------------------------------------------------
# API
# --------------------------------------------------------


def validate(
    view: PresenterView,
    event: InputEvent,
    services: ServiceDirectory,
) -> ValidationResult:

    policy = services.get(PolicyService)

    values: dict[str, Any] = {}
    errors: dict[str, list[FieldError]] = {}

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


# --------------------------------------------------------
# VIEW UPDATE
# --------------------------------------------------------


def apply_errors(
    pv: PresenterView,
    errors: dict[str, list[FieldError]],
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
                updated_fields.append(f.clear_errors())

        new_blocks.append(replace(block, fields=updated_fields))

    return pv.body_only(new_blocks)
