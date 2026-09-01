"""LocalTransport exposes the session CREATE/RESUME contract to clients.

A keyless connect creates a session and the client learns its key through
ClientConnection.session_key; connecting with that key resumes the same
session (live runner and after cleanup).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from y5n.runtime.api.naming import Key
from y5n.runtime.api.runtime import RuntimeInfo
from y5n.runtime.engine.machine.manager import RuntimeManager
from y5n.runtime.engine.machine.runner import Runner
from y5n.runtime.engine.machine.session import SessionBuilder
from y5n.runtime.engine.runtime.sessions.service import SessionService
from y5n.runtime.engine.transport.local import LocalTransport


class _MemoryRow:
    def __init__(self, key: Key, doc: dict | None):
        self.key = key
        self.ok = doc is not None
        self._doc = doc

    def require_object(self) -> dict:
        assert self._doc is not None
        return self._doc


class MemorySessionStore:
    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}

    async def on_replace(self, *, key, doc, snapshot_hint=None, expected_rev=None):
        self.docs[str(key)] = dict(doc)

    async def on_get(self, *, key, at_time=None):
        return _MemoryRow(key, self.docs.get(str(key)))


def _make_manager(store: MemorySessionStore) -> RuntimeManager:
    svc = SessionService(on_replace=store.on_replace, on_get=store.on_get)

    async def on_get_session(*, key: Key):
        from y5n.runtime.engine.runtime.sessions.session import Session

        session, _ = await svc.get_or_create(key)
        return session

    async def on_resume_session(key: Key):
        from y5n.runtime.engine.runtime.sessions.session import Session

        session = await svc.get(key)
        if session is None:
            raise RuntimeError(f"Session {key} not found")
        return session

    builder = SessionBuilder(on_get_session=on_get_session)
    return RuntimeManager(
        on_schedule=AsyncMock(),
        on_get_session=builder.create,
        on_resume_session=on_resume_session,
        on_create_runner=MagicMock(
            side_effect=lambda *, session: Runner(
                session=session,
                on_dispatch=AsyncMock(),
                on_schedule_flow=MagicMock(),
            )
        ),
        on_setup=AsyncMock(),
        info=RuntimeInfo(version="test"),
    )


@pytest.mark.asyncio
async def test_local_transport_exposes_and_reuses_session_key():
    store = MemorySessionStore()
    manager = _make_manager(store)
    transport = LocalTransport(manager)

    # CREATE: keyless connect assigns a key and exposes it on the connection
    conn1 = await transport.connect(AsyncMock())
    assert conn1.session_key is not None
    first_key = Key.from_str(conn1.session_key)
    first_session = manager._sessions[first_key].session

    # RESUME while the runner is live: same session reused, same key assigned
    conn2 = await transport.connect(AsyncMock(), session_key=conn1.session_key)
    assert conn2.session_key == conn1.session_key
    assert manager._sessions[Key.from_str(conn2.session_key)].session is first_session

    # RESUME after the runner was cleaned up: same session comes back
    await manager.disconnect(conn1)
    await manager.disconnect(conn2)
    conn3 = await transport.connect(AsyncMock(), session_key=conn1.session_key)
    assert conn3.session_key == conn1.session_key
    assert manager._sessions[Key.from_str(conn3.session_key)].session is first_session

    # store reflects the session (persisted by the service)
    assert conn1.session_key in store.docs
