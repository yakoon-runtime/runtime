from __future__ import annotations

from typing import Protocol

from yakoon.base.naming import Namespace
from yakoon.base.plugins.models import AuthResult

from ..models import Account


class AuthenticationService:

    def __init__(
        self,
        on_get_account: OnGetAccount,
        on_verify_account: OnVerifyAccount,
    ):
        self.on_get_account = on_get_account
        self.on_verify = on_verify_account

    async def authenticate(
        self, namespace: Namespace, username: str, secret: str
    ) -> AuthResult:

        acc = await self.on_get_account(namespace=namespace, username=username)
        if not acc:
            return AuthResult(ok=False, reason="unknown-user")

        if not self.on_verify(account=acc, secret=secret):
            return AuthResult(ok=False, reason="invalid-credentials")

        return AuthResult(ok=True, account=self._to_dict(acc))

    def _to_dict(self, account: Account) -> dict:
        return {
            "key": account.key,
            "username": account.username,
            "roles": list(account.roles),
            "permissions": list(account.permissions),
        }


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetAccount(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        username: str,
    ) -> Account | None: ...


class OnVerifyAccount(Protocol):
    def __call__(
        self,
        *,
        account: Account,
        secret: str,
    ) -> bool: ...
