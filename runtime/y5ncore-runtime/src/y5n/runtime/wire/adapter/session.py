"""Adapter: session.* ports for the Runtime Bus.

Converts SDK-style calls into internal host operations:

* ``attach(target_key=..., session_key=...)``
* ``detach(session_key=...)``
* ``update(session_key=..., patch={...})``
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from y5n.base.naming.key import Key
from y5n.base.runtime.context import Call
from y5n.runtime.runtime import Session

_PATCH_MAP: dict[str, str] = {
    "cwd": "current_path",
    "locale": "lang",
    "user_key": "user_key",
    "user_name": "user_name",
}


class SessionAdapter:
    """SDK-facing session.attach / session.detach / session.update Port."""

    def __init__(
        self,
        host,
        on_save: Callable[..., Awaitable[None]] | None = None,
    ) -> None:
        self._host = host
        self._on_save = on_save

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

    async def update(
        self, call: Call, *, session_key: str, patch: dict[str, Any]
    ) -> dict[str, Any]:
        runner = self._host._sessions.get(Key.from_str(session_key))
        if runner is None:
            raise RuntimeError(f"Session {session_key} not found")

        session: Session = runner.session
        applied: dict[str, Any] = {}
        ignored: dict[str, Any] = {}

        for key, value in patch.items():
            internal = _PATCH_MAP.get(key)
            if internal is None:
                ignored[key] = value
                continue
            setattr(session.data, internal, value)
            applied[key] = value

        if self._on_save and applied:
            await self._on_save(session=session)

        return {"applied": applied, "ignored": ignored}
