from __future__ import annotations

from typing import Protocol

from y5n.api.naming import Namespace
from y5n.api.ports.models import AuthResult

from ...models.ident import User


class AuthenticationService:

    def __init__(
        self,
        on_get_user: OnGetUser,
        on_verify_user: OnVerifyUser,
    ):
        self.on_get_user = on_get_user
        self.on_verify = on_verify_user

    async def authenticate(
        self, namespace: Namespace, username: str, secret: str
    ) -> AuthResult:

        user = await self.on_get_user(namespace=namespace, username=username)
        if not user:
            return AuthResult(ok=False, reason="unknown-user")

        if not self.on_verify(user=user, secret=secret):
            return AuthResult(ok=False, reason="invalid-credentials")

        return AuthResult(ok=True, user=self._to_dict(user))

    def _to_dict(self, user: User) -> dict:
        return {
            "key": user.key,
            "username": user.username,
        }


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetUser(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        username: str,
    ) -> User | None: ...


class OnVerifyUser(Protocol):
    def __call__(
        self,
        *,
        user: User,
        secret: str,
    ) -> bool: ...
