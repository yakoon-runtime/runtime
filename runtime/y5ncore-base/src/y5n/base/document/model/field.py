from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class SelectOption:
    value: str
    label: str


class FieldType(StrEnum):
    INT = "int"
    BOOL = "bool"
    DATE = "date"
    TIME = "time"
    FLOAT = "float"
    STRING = "string"
    DATETIME = "datetime"


@dataclass(frozen=True, slots=True)
class FieldError:
    message: str
    code: str | None = None


FieldsState = Literal["idle", "active", "done"]


@dataclass(frozen=True, slots=True)
class Field:
    """Canonical field definition used by FieldsBlock."""

    policy: str
    title: str | None = None
    required: bool = False
    name: str | None = None

    hint: str | None = None
    default: str | None = None
    pattern: str | None = None

    error: str | None = None
    ui: dict[str, Any] | None = None

    type: FieldType | None = None
    lookup: str | None = None
    options: list[SelectOption] | None = None

    # ------------------------
    # Runtime State
    # ------------------------

    state: FieldsState = "idle"
    value: Any | None = None
    query: Any | None = None
    errors: tuple[FieldError, ...] = ()

    def with_value(self, value: Any) -> Field:
        return replace(self, value=value)

    def with_errors(self, errors: list[FieldError]) -> Field:
        return replace(self, errors=tuple(errors))

    def clear_errors(self) -> Field:
        return replace(self, errors=())

    def has_errors(self) -> bool:
        return bool(self.errors)

    def display_label(self) -> str:
        return self.title or "Unnamed"
