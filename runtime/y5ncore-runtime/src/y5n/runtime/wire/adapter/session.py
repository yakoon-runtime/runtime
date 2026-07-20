"""Adapter: session.* ports for the Runtime Bus.

Converts SDK-style ``attach(target_key=..., session_key=...)`` and
``detach(session_key=...)`` calls into internal host operations.
"""

from __future__ import annotations

from y5n.base.naming.key import Key
from y5n.base.runtime.context import Call


class SessionAdapter:
    """SDK-facing session.attach / session.detach Port."""

    def __init__(self, host) -> None:
        self._host = host

    async def attach(self, call: Call, *, session_key: str, target_key: str) -> None:
        runner = self._host._sessions.get(Key.from_str(session_key))
        if runner is None:
            raise RuntimeError(f"Session {session_key} not found")
        await self._host.attach_session(runner.session, target_key)

    async def detach(self, call: Call, *, session_key: str) -> None:
        runner = self._host._sessions.get(Key.from_str(session_key))
        if runner is None:
            raise RuntimeError(f"Session {session_key} not found")
        await self._host.detach_session(runner.session)
