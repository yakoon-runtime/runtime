"""Session restart contract: CREATE vs. explicit RESUME.

Contract (decided):
- a keyless connect always creates a new session; it can never collide
  with a session document persisted by an earlier runtime process
- connect(session_key=X) means explicit resume: X must already exist —
  live in this process (authentication lives) or persisted by an earlier
  process (authentication and elevation die, interaction state is kept,
  the invalidation is persisted immediately)
- an unknown resume key fails with the existing "Session ... not found"
  idiom instead of creating a session under it
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from y5n.runtime.api.clients import ClientConnection, SessionNotFound
from y5n.runtime.api.naming import Key
from y5n.runtime.api.runtime import RuntimeInfo
from y5n.runtime.engine.machine.manager import RuntimeManager
from y5n.runtime.engine.machine.runner import Runner
from y5n.runtime.engine.machine.session import SessionBuilder
from y5n.runtime.engine.runtime.sessions.service import SessionService
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData
from y5n.runtime.engine.services.permissions import PermissionParser, PermissionSet

PERSISTED_KEY = Key.from_parts("system", "session", "runtime", "old-0")


def _fake_connection() -> ClientConnection:
    return ClientConnection(
        emit=AsyncMock(),
        dispatch=AsyncMock(),
    )


class _MemoryRow:
    """GetResult stand-in over the in-memory document store."""

    def __init__(self, key: Key, doc: dict | None):
        self.key = key
        self.ok = doc is not None
        self._doc = doc

    def require_object(self) -> dict:
        assert self._doc is not None
        return self._doc


class MemorySessionStore:
    """Minimal on_get/on_replace pair over a dict (store contract shape)."""

    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}

    async def on_replace(self, *, key, doc, snapshot_hint=None, expected_rev=None):
        self.docs[str(key)] = dict(doc)

    async def on_get(self, *, key, at_time=None):
        return _MemoryRow(key, self.docs.get(str(key)))


def _seed_authenticated(store: MemorySessionStore) -> None:
    """A session document as a previous process would have persisted it."""
    store.docs[str(PERSISTED_KEY)] = {
        "current_path": "/opt/contacts",
        "user_key": "acc-key-root",
        "user_name": "root",
        "security_context": "administrative",
        "last_active": None,
        "lang": "de",
        "debug": True,
        "data": {"fs:root": "/workspace", "luma.current_world": "w1"},
        "_v": 1,
    }


def _make_runtime(store: MemorySessionStore) -> tuple[RuntimeManager, SessionService]:
    """A fresh 'runtime process': new identity map over the same store.

    Mirrors the wire: keyless connects go through the real SessionBuilder
    into get_or_create; explicit resume goes through SessionService.get
    and fails on an unknown key — never through get_or_create.
    """
    svc = SessionService(on_replace=store.on_replace, on_get=store.on_get)

    async def on_get_session(*, key: Key) -> Session:
        session, _ = await svc.get_or_create(key)
        return session

    async def on_resume_session(key: Key) -> Session:
        session = await svc.get(key)
        if session is None:
            raise SessionNotFound(f"Session {key} not found")
        return session

    builder = SessionBuilder(on_get_session=on_get_session)
    manager = RuntimeManager(
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
    return manager, svc


@pytest.mark.asyncio
async def test_keyless_create_never_resumes_persisted_session():
    """A keyless connect creates a fresh anonymous session even though the
    store holds a document persisted under the old deterministic key; the
    persisted document itself is untouched."""
    store = MemorySessionStore()
    _seed_authenticated(store)

    manager, _svc = _make_runtime(store)
    conn = _fake_connection()
    session = await manager.connect(conn)

    assert str(session.key) != str(PERSISTED_KEY)
    assert session.data.user_key is None
    assert session.data.user_name is None
    assert session.is_authenticated is False
    assert session.security_context == "normal"
    # the persisted document is untouched by a keyless connect
    assert store.docs[str(PERSISTED_KEY)]["user_key"] == "acc-key-root"


@pytest.mark.asyncio
async def test_resume_after_process_boundary_invalidates_and_persists():
    """Resume of a persisted session crosses the process boundary: the
    interaction state is restored while authentication, elevation state
    and permissions are invalidated — and the invalidation is persisted,
    so the store matches the live session (idempotent across resumes)."""
    store = MemorySessionStore()
    _seed_authenticated(store)

    manager, _svc = _make_runtime(store)
    conn = _fake_connection()
    session = await manager.connect(conn, session_key=PERSISTED_KEY)

    # interaction state restored
    assert session.cwd == "/opt/contacts"
    assert session.data.lang == "de"
    assert session.get_data("fs:root") == "/workspace"
    assert session.get_data("luma.current_world") == "w1"

    # authentication and elevation invalidated
    assert session.data.user_key is None
    assert session.data.user_name is None
    assert session.is_authenticated is False
    assert session.security_context == "normal"
    assert list(session.permissions) == []

    # the invalidation is persisted: store matches live
    doc = store.docs[str(PERSISTED_KEY)]
    assert doc["user_key"] is None
    assert doc["user_name"] is None
    assert doc["security_context"] == "normal"
    assert doc["current_path"] == "/opt/contacts"
    assert doc["data"]["fs:root"] == "/workspace"

    # a second 'process' resumes the now-anonymous document — idempotent
    manager2, _svc2 = _make_runtime(store)
    conn2 = _fake_connection()
    session2 = await manager2.connect(conn2, session_key=PERSISTED_KEY)
    assert session2.data.user_key is None
    assert session2.security_context == "normal"
    assert session2.cwd == "/opt/contacts"


@pytest.mark.asyncio
async def test_same_process_resume_preserves_authentication():
    """Within one process the identity map is the boundary: a reconnect
    with a session key (live runner or cleaned-up runner) keeps the
    authenticated identity, permissions and security context."""
    store = MemorySessionStore()
    manager, _svc = _make_runtime(store)

    conn = _fake_connection()
    session = await manager.connect(conn)

    # authenticate like ident would (live state)
    session.set_identity("acc-key-stefan", "stefan")
    permset = PermissionSet()
    permset.add(PermissionParser().parse("/usr/bin|rwx"))
    session.set_permissions(permset)

    # (a) reconnect while the runner is still live
    conn2 = _fake_connection()
    resumed = await manager.connect(conn2, session_key=session.key)
    assert resumed.data.user_key == "acc-key-stefan"
    assert list(resumed.permissions) != []

    # (b) reconnect after the runner was cleaned up (no subscribers)
    await manager.disconnect(conn)
    await manager.disconnect(conn2)
    conn3 = _fake_connection()
    resumed2 = await manager.connect(conn3, session_key=session.key)
    assert resumed2.data.user_key == "acc-key-stefan"
    assert resumed2.data.user_name == "stefan"
    assert resumed2.security_context == "normal"
    assert list(resumed2.permissions) != []


@pytest.mark.asyncio
async def test_resume_unknown_key_fails_without_creating_state():
    """An unknown resume key fails with the existing not-found idiom and
    creates neither a store document nor a live runner."""
    store = MemorySessionStore()
    manager, _svc = _make_runtime(store)

    missing = Key.from_parts("system", "session", "runtime", "missing")
    conn = _fake_connection()
    with pytest.raises(SessionNotFound, match="not found") as excinfo:
        await manager.connect(conn, session_key=missing)

    # machine-readable, yet still caught by every existing RuntimeError handler
    assert excinfo.value.code == "session_not_found"
    assert isinstance(excinfo.value, RuntimeError)

    assert str(missing) not in store.docs
    assert missing not in manager._sessions
