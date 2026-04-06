from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class InputContextRef:
    id: str
    last: str | None = None


@dataclass(frozen=True, slots=True)
class InputContext:
    context_id: str | None = None
    open_contexts: list[InputContextRef] = field(default_factory=list)
