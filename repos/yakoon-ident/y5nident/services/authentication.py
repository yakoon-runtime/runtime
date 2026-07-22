from __future__ import annotations

from typing import Protocol

from y5n.api.naming import Namespace
from y5n.api.ports import OnAfterVerify

from ..models import User


class AuthenticationService:

    def __init__(
        self,
        on_get_user: OnGetUser,
        on_verify_user: OnVerifyUser,
        on_after_verify: OnAfterVerify,
        namespace: Namespace,
    ):
        self.on_get_user = on_get_user
        self.on_verify = on_verify_user
        self.on_after_verify = on_after_verify
        self._namespace = namespace

    async def authenticate(
        self, *, username: str, secret: str, session_key: str | None = None
    ) -> dict:

        user = await self.on_get_user(namespace=self._namespace, username=username)
        if not user:
            return {"ok": False, "reason": "unknown-user"}

        if not self.on_verify(user=user, secret=secret):
            return {"ok": False, "reason": "invalid-credentials"}

        after = await self.on_after_verify(user=user)

        if session_key:
            from y5n.sdk import ports

            patch = {
                "user_key": str(user.key),
                "user_name": user.username,
            }
            await ports.get("session").update(session_key=session_key, patch=patch)

        return {
            "ok": True,
            "user": self._to_dict(user),
            "after": after,
        }

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
