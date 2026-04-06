from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class InputContextRef:
    command: str | None = None
    context_id: str | None = None


@dataclass(frozen=True, slots=True)
class InputContext:
    command: str | None = None
    context_id: str | None = None
    open_contexts: list[InputContextRef] = field(default_factory=list)
    ui: dict[str, Any] = field(default_factory=dict)
