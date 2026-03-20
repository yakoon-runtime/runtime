from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextInput:
    value: str


@dataclass(frozen=True)
class FormInput:
    data: dict[str, object]


InputEvent = TextInput | FormInput

# TODO: Statt der Unterscheidung.

"""
class __InputEvent:
    def to_values(self) -> dict
    def to_text(self) -> str

    """
