from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ViewFieldDef:
    """
    Describes one input field as authored in a View template.

    Note:
        - It's the canonical authoring-time definition used in ViewSpec.input.
    """

    policy: str
    title: str | None = None
    required: bool = False
    var: str | None = None

    hint: str = ""
    default: str = ""
    pattern: str = ""

    ui: dict[str, Any] | None = None  # <- neu

    # Optional extensions (keep cheap):
    type: str | None = None  # e.g. "string", "int" (if you want)
    options: list[dict[str, str]] | None = None  # e.g. [{"value":"x","label":"X"}]
