from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InputContext:
    origin: str | None = None
    echo: str | None = None
