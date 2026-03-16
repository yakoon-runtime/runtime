# yakoon/platform/host/registry.py

from __future__ import annotations


class SessionRegistry:
    """
    Holds all active sessions on the host.
    """

    def __init__(self):
        self._sessions: dict[str, object] = {}

    def add(self, session_id: str, session: object) -> None:
        self._sessions[session_id] = session

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def get(self, session_id: str) -> object | None:
        return self._sessions.get(session_id)

    def list(self):
        return list(self._sessions.keys())
