"""Adapter: session.* ports for the Runtime Bus.

Converts SDK-style calls into internal manager operations:

* ``attach(target_key=..., session_key=...)``
* ``detach(session_key=...)``
* ``update(session_key=..., patch={...})``
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from y5n.runtime.api.naming.key import Key
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.capabilities.permission import PermissionParser
from y5n.runtime.engine.runtime import Session

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
        manager,
        on_save: Callable[..., Awaitable[None]] | None = None,
    ) -> None:
        self._manager = manager
        self._on_save = on_save

    async def attach(self, call: Call, *, session_key: str, target_key: str) -> None:
        runner = self._manager._sessions.get(Key.from_str(session_key))
        if runner is None:
            raise RuntimeError(f"Session {session_key} not found")
        await self._manager.attach_session(runner.session, target_key)

    async def detach(self, call: Call, *, session_key: str) -> None:
        runner = self._manager._sessions.get(Key.from_str(session_key))
        if runner is None:
            raise RuntimeError(f"Session {session_key} not found")
        await self._manager.detach_session(runner.session)

    async def logout(self, call: Call) -> None:
        session_key = call.caller_session_key
        if not session_key:
            raise RuntimeError("caller_session_key is required")

        runner = self._manager._sessions.get(Key.from_str(session_key))
        if runner is None:
            raise RuntimeError(f"Session {session_key} not found")

        runner.session.logout()
        runner.session.set_permissions(self._empty_permissions())
        if self._on_save:
            await self._on_save(session=runner.session)

    def _empty_permissions(self):
        from y5n.runtime.engine.capabilities.permission import PermissionSet

        return PermissionSet()

    async def set_permissions(self, call: Call, *, specs: list[str]) -> dict[str, int]:
        """Set the caller session's permissions from serializable spec strings.

        The ident pack resolves the account's effective permissions into
        spec strings (e.g. "/crm/contact/edit|rwx"); the engine parses them
        into a PermissionSet. The pack never touches engine internals.
        """
        session_key = call.caller_session_key
        if not session_key:
            raise RuntimeError("caller_session_key is required")

        runner = self._manager._sessions.get(Key.from_str(session_key))
        if runner is None:
            raise RuntimeError(f"Session {session_key} not found")

        parser = PermissionParser()
        permset = self._empty_permissions()
        for spec in specs or []:
            permset.add(parser.parse(spec))

        runner.session.set_permissions(permset)
        return {"granted": len(specs or [])}

    async def update(self, call: Call, *, patch: dict[str, Any]) -> dict[str, Any]:
        session_key = call.caller_session_key
        if not session_key:
            raise RuntimeError("caller_session_key is required")

        runner = self._manager._sessions.get(Key.from_str(session_key))
        if runner is None:
            raise RuntimeError(f"Session {session_key} not found")

        session: Session = runner.session
        applied: dict[str, Any] = {}
        ignored: dict[str, Any] = {}

        for key, value in patch.items():
            internal = _PATCH_MAP.get(key)
            if internal is not None:
                setattr(session.data, internal, value)
                applied[key] = value
            elif key == "data" and isinstance(value, dict):
                for dk, dv in value.items():
                    session.data.set(dk, dv)
                applied[key] = value
            else:
                ignored[key] = value

        if self._on_save and applied:
            await self._on_save(session=session)

        return {"applied": applied, "ignored": ignored}

    async def current(self, call: Call) -> dict[str, Any]:
        """Return the live Session state for the caller's session key."""
        session_key = call.caller_session_key
        if not session_key:
            raise RuntimeError("caller_session_key is required")

        runner = self._manager._sessions.get(Key.from_str(session_key))
        if runner is None:
            raise RuntimeError(f"Session {session_key} not found")

        session: Session = runner.session
        return {
            "key": str(session.key),
            "lang": session.lang,
            "user_name": session.user_name,
            "user_id": str(session.get_identity()) if session.get_identity() else None,
            "data": dict(session.data.data),
        }
