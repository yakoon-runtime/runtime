from __future__ import annotations

import uuid
from itertools import count
from typing import Protocol

from y5n.runtime.api.naming import Key
from y5n.runtime.engine.runtime import Session


class SessionBuilder:
    """Factory for creating runtime Session objects.

    Generates unique session keys and delegates to the OnGetSession port.
    Keys embed a per-boot random id, so a keyless connect can never
    collide with a session document persisted by an earlier process —
    creating is the only thing a keyless connect can do.
    """

    def __init__(
        self,
        on_get_session: OnGetSession,
    ):
        self.on_get_session = on_get_session
        self._boot = uuid.uuid4().hex
        self._counter = count(0)

    async def create(self) -> Session:
        key = self._next_key()
        session = await self.on_get_session(key=key)

        return session

    def _next_key(self) -> Key:
        return Key.from_parts(
            "system",
            "session",
            "runtime",
            f"{self._boot}-{next(self._counter)}",
        )


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetSession(Protocol):
    async def __call__(self, *, key: Key) -> Session: ...


class OnResumeSession(Protocol):
    async def __call__(self, key: Key) -> Session: ...
