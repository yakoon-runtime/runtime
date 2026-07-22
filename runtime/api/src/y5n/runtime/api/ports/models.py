from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True, slots=True)
class AuthResult:
    ok: bool
    user: dict | None = None
    reason: str | None = None
    after: dict | None = None


class HealthLevel(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class HealthResult:
    level: HealthLevel
    message: str | None = None
    children: list[HealthResult] = field(default_factory=list)

    @classmethod
    def green(cls, message: str | None = None) -> HealthResult:
        return cls(level=HealthLevel.GREEN, message=message)

    @classmethod
    def yellow(cls, message: str) -> HealthResult:
        return cls(level=HealthLevel.YELLOW, message=message)

    @classmethod
    def red(cls, message: str) -> HealthResult:
        return cls(level=HealthLevel.RED, message=message)


__all__ = [
    "AuthResult",
    "HealthLevel",
    "HealthResult",
]
