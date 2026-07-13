from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthResult:
    ok: bool
    user: dict | None = None
    reason: str | None = None
    after: dict | None = None


__all__ = [
    "AuthResult",
]
