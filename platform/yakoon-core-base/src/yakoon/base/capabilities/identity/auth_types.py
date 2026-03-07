from dataclasses import dataclass

from .account import Account


@dataclass(frozen=True, slots=True)
class AuthResult:
    ok: bool
    account: Account | None = None
    reason: str | None = None
