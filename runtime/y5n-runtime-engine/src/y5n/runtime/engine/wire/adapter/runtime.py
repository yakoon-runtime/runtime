"""Adapter: runtime.* ports for the Runtime Bus.

Exposes scheduler queries to the SDK as ordinary service calls:

* ``flows(exclude_id=...)`` — list active flows
* ``background()`` — clear the foreground flow

The session is resolved from the caller's session key, following the
same pattern as the session adapter.
"""

from __future__ import annotations

from y5n.runtime.api.naming.key import Key
from y5n.runtime.api.runtime.context import Call


class RuntimeAdapter:
    """SDK-facing runtime.flows / runtime.background Port."""

    def __init__(self, manager) -> None:
        self._manager = manager

    def _resolve_session(self, call: Call):
        session_key = call.caller_session_key
        if not session_key:
            raise RuntimeError("caller_session_key is required")
        runner = self._manager._sessions.get(Key.from_str(session_key))
        if runner is None:
            raise RuntimeError(f"Session {session_key} not found")
        return runner.session

    async def flows(self, call: Call, *, exclude_id: str | None = None) -> list[dict]:
        session = self._resolve_session(call)
        result = []
        fg = session.foreground_flow
        for idx, flow in enumerate(session.flows(exclude=exclude_id), start=1):
            result.append(
                {
                    "index": idx,
                    "id": flow.id,
                    "label": flow.node.name or flow.node.key,
                    "state": flow.control.label() if flow.control else "run",
                    "foreground": bool(fg) and fg.id == flow.id,
                }
            )
        return result

    async def background(self, call: Call) -> dict | None:
        session = self._resolve_session(call)
        fg = session.foreground_flow
        if not fg:
            return None
        session.set_foreground_flow(None)
        return {"id": fg.id, "label": fg.node.name or fg.node.key}
