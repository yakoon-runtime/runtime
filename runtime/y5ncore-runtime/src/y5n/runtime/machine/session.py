from __future__ import annotations

from itertools import count
from typing import Protocol

from y5n.base.naming import Key
from y5n.runtime.runtime import Session


class SessionBuilder:
    """Factory for creating runtime Session objects.

    Generates unique session keys and delegates to the OnGetSession port.
    """

    def __init__(
        self,
        on_get_session: OnGetSession,
    ):
        self.on_get_session = on_get_session
        self._counter = count(0)

    async def create(self) -> Session:
        key = self._next_key()
        print(f"[DEBUG:] Session_key: {key}")

        session = await self.on_get_session(key=key)

        return session

    def _next_key(self) -> Key:
        return Key.from_parts(
            "system",
            "session",
            "runtime",
            str(next(self._counter)),
        )


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetSession(Protocol):
    async def __call__(self, *, key: Key) -> Session: ...
