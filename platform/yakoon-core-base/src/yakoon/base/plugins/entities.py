from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthResult:
    ok: bool
    account: dict | None = None
    reason: str | None = None
