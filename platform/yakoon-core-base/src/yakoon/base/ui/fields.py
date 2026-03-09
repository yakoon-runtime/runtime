from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


@dataclass(frozen=True, slots=True)
class SelectOption:
    value: str
    label: str


class FieldType(StrEnum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    DATE = "date"
    SELECT = "select"


@dataclass(frozen=True, slots=True)
class ViewFieldDef:
    """
    Canonical field definition used by FieldsBlock.
    """

    policy: str
    title: str | None = None
    required: bool = False
    var: str | None = None

    hint: str = ""
    default: str = ""
    pattern: str = ""

    ui: dict[str, Any] | None = None

    type: FieldType | None = None
    options: list[SelectOption] | None = None
