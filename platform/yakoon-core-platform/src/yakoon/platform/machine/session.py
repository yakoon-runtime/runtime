from __future__ import annotations

from typing import Protocol

from yakoon.base.naming import Key
from yakoon.platform.runtime import Session


class SessionBuilder:

    def __init__(
        self,
        on_get_session: OnGetSession,
        on_apply_permissions: OnApplyPermissions,
    ):
        self.on_get_session = on_get_session
        self.on_apply_permissions = on_apply_permissions
        self._counter = 0

    async def create(self) -> Session:
        key = self._next_key()

        session = await self.on_get_session(key=key)
        self.on_apply_permissions(session=session)

        return session

    def _next_key(self) -> Key:
        self._counter += 1
        return Key.from_parts(
            "system",
            "session",
            "runtime",
            str(self._counter),
        )


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetSession(Protocol):
    async def __call__(self, *, key: Key) -> Session: ...


class OnApplyPermissions(Protocol):
    def __call__(self, *, session: Session): ...
