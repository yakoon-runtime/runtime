from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from yakoon.base.capabilities.interaction import FieldPolicyEngine
from yakoon.base.projection import Projection, ProjectionQuery
from yakoon.base.projection.model import FieldError
from yakoon.base.runtime import Container
from yakoon.base.runtime.input import InputEvent


@dataclass
class ValidationResult:
    ok: bool
    values: dict[str, Any]
    errors: dict[str, list[FieldError]]


# --------------------------------------------------------
# API
# --------------------------------------------------------


def validate(
    projection: Projection,
    event: InputEvent,
    container: Container,
) -> ValidationResult:

    policy = container.get(FieldPolicyEngine)

    values: dict[str, Any] = {}
    errors: dict[str, list[FieldError]] = {}

    raw_values = event.to_values()

    query = ProjectionQuery.from_projection(projection)
    for field in query.bound_fields():
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
    projection: Projection,
    errors: dict[str, list[FieldError]],
) -> Projection:

    new_blocks = []

    query = ProjectionQuery.from_projection(projection)
    for block in query.get_blocks():
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

    return projection.body_only(new_blocks)
