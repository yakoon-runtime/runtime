from __future__ import annotations

from y5n.runtime.engine.naming import Key

from .session import Session


class SessionIdentityMap:

    def __init__(self) -> None:
        self._live: dict[str, Session] = {}

    def get(self, key: Key) -> Session | None:
        return self._live.get(str(key))

    def put(self, session: Session) -> None:
        self._live[str(session.key)] = session

    def release(self, key: Key) -> None:
        self._live.pop(str(key), None)

    def clear(self) -> None:
        self._live.clear()
