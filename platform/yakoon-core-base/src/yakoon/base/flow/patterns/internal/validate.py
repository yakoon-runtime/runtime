from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from yakoon.base.projection import Projection, ProjectionQuery
from yakoon.base.projection.model import FieldError
from yakoon.base.runtime import InputEvent

from ...context import DslContext


@dataclass
class ValidationResult:
    ok: bool
    values: dict[str, Any]
    errors: dict[str, list[FieldError]]


# --------------------------------------------------------
# API
# --------------------------------------------------------


def validate(
    context: DslContext,
    projection: Projection,
    event: InputEvent,
) -> ValidationResult:

    values: dict[str, Any] = {}
    errors: dict[str, list[FieldError]] = {}

    raw_values = event.to_values()

    query = ProjectionQuery.from_projection(projection)
    for field in query.bound_fields():
        if field.var is None:
            continue

        raw = raw_values.get(field.var)

        # ----------------------------------------
        # 1. SELECT / OPTIONS (Closed world)
        # ----------------------------------------
        if field.options and isinstance(raw, str):

            # build lookup (case-insensitive)
            label_map = {opt.label.lower(): opt.value for opt in field.options}
            value_map = {opt.value.lower(): opt.value for opt in field.options}

            raw_lower = raw.lower()

            # resolve input
            if raw_lower in label_map:
                resolved = label_map[raw_lower]
            elif raw_lower in value_map:
                resolved = value_map[raw_lower]
            else:
                if field.error:
                    errors[field.var] = [FieldError(message=field.error)]
                else:
                    errors[field.var] = [FieldError(message="Invalid option")]
                continue

            # policy prüft nur Typ, NICHT Erweiterung
            result = context.policies.validate(
                policy_key=field.policy,
                raw=resolved,
            )

            if result.ok:
                values[field.var] = result.value
            else:
                if field.error:
                    errors[field.var] = [FieldError(message=field.error)]
                else:
                    errors[field.var] = [
                        FieldError(message=e.message) for e in result.errors
                    ]

            continue

        # ----------------------------------------
        # 2. FREITEXT (open world)
        # ----------------------------------------
        result = context.policies.validate(
            policy_key=field.policy,
            raw=raw,
        )

        if result.ok:
            values[field.var] = result.value
        else:
            if field.error:
                errors[field.var] = [FieldError(message=field.error)]
            else:
                errors[field.var] = [
                    FieldError(message=e.message) for e in result.errors
                ]

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

    return projection.with_body(new_blocks)
