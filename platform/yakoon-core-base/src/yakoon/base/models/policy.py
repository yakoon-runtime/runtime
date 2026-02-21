from dataclasses import dataclass, replace
from typing import Any, TypeAlias

from yakoon.base.models.fields import FieldType


@dataclass(frozen=True, slots=True)
class FieldPolicy:
    key: str
    type: FieldType
    required: bool = False
    secret: bool = False
    hint: str = ""
    pattern: str = ""
    default: Any = None
    options: list[dict] | None = None
    validators: tuple[str, ...] = ()

    def fork(self, **changes) -> "FieldPolicy":
        return replace(self, **changes)


RawValue: TypeAlias = object
CoercedValue: TypeAlias = object


@dataclass(frozen=True, slots=True)
class PolicyValidationError:
    field_key: str
    message: str


@dataclass(frozen=True, slots=True)
class PolicyValidationResult:
    ok: bool
    value: object | None = None
    errors: list[PolicyValidationError] = ()
