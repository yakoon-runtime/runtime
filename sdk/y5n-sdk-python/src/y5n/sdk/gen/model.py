"""Intermediate representation for generated schema models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PropertyDef:
    """A single property of a generated class."""

    name: str
    type_ref: str
    required: bool = False
    default: Any = None
    nullable: bool = False
    const: str | None = None
    enum_values: list[str] | None = None
    items_ref: str | None = None


@dataclass
class ClassDef:
    """A generated class definition."""

    name: str
    type_value: str | None
    base: str | None
    properties: list[PropertyDef]
    description: str = ""
    is_root: bool = False


@dataclass
class Schema:
    """Top-level schema holding all generated classes."""

    classes: list[ClassDef] = field(default_factory=list)
