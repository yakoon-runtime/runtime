"""Live-session regression (ADR-12: the Session is a live reference).

The session is shared, mutable state. A flow that reads session data must
see mutations made by *other* flows — this is what makes a long-running
task observe a logout. `session.current()` goes over the Bus to the live
SessionService; the invocation context only carries the session key.

These tests drive the SessionAdapter.current() port end-to-end.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from y5n.runtime.api.clients import ClientConnection
from y5n.runtime.api.naming import Key
from y5n.runtime.api.runtime import RuntimeInfo
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.machine.manager import RuntimeManager
from y5n.runtime.engine.machine.runner import Runner
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData
from y5n.runtime.engine.wire.adapter.session import SessionAdapter

_COUNTER = 0


def _unique_key() -> Key:
    global _COUNTER
    _COUNTER += 1
    return Key.from_parts("test", "session", "runtime", f"live{_COUNTER}")


def _fake_connection() -> ClientConnection:
    return ClientConnection(emit=AsyncMock(), dispatch=AsyncMock())


def _call_for(session_key: str) -> Call:
    return Call(
        port="session",
        method="current",
        caller_path="",
        caller_session_key=session_key,
    )


@pytest.fixture
async def adapter():
    manager = RuntimeManager(
        on_schedule=AsyncMock(),
        on_get_session=AsyncMock(
            side_effect=lambda: Session(key=_unique_key(), data=SessionData())
        ),
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
    yield SessionAdapter(manager, on_save=AsyncMock())


@pytest.mark.asyncio
async def test_session_current_returns_live_data(adapter):
    """current() reflects mutations made by another flow (logout)."""

    # A connection creates a session; its data carries a marker.
    conn = _fake_connection()
    session = await adapter._manager.connect(conn)
    session.data.set("app.flag", "set-by-flow-a")
    session.data.set("app.user", "alice")

    result = await adapter.current(_call_for(str(session.key)))
    assert result["key"] == str(session.key)
    assert result["data"]["app.flag"] == "set-by-flow-a"
    assert result["data"]["app.user"] == "alice"


@pytest.mark.asyncio
async def test_session_current_sees_logout_from_other_flow(adapter):
    """A long-running flow sees a logout performed by another flow.

    The logout goes through the same Bus port a second flow would call
    (session.logout) — not by mutating the session directly. Flow A reads
    before, Flow B logs out, Flow A reads again and sees the change.
    """

    conn_a = _fake_connection()
    session = await adapter._manager.connect(conn_a)
    session.set_identity(Key.from_parts("users", "user", "global", "u-1"), "alice")

    # Flow A reads before: current() reports the identity.
    before = await adapter.current(_call_for(str(session.key)))
    assert before["user_id"] is not None
    assert before["user_name"] == "alice"

    # Flow B (another connection, same session) logs out via the Bus port.
    conn_b = _fake_connection()
    await adapter._manager.connect(conn_b, session_key=session.key)
    await adapter.logout(
        Call(
            port="session",
            method="logout",
            caller_path="",
            caller_session_key=str(session.key),
        )
    )

    # Flow A reads again — a fresh live lookup sees the logout.
    after = await adapter.current(_call_for(str(session.key)))
    assert after["user_id"] is None
    assert after["user_name"] is None


@pytest.mark.asyncio
async def test_session_current_unknown_key_raises(adapter):
    """current() with an unknown session key is an error, not a silent empty."""

    with pytest.raises(RuntimeError):
        await adapter.current(_call_for("system/session/runtime#missing"))


@pytest.mark.asyncio
async def test_security_context_lifecycle(adapter):
    """security_context flows through current/patch/logout end to end."""

    conn = _fake_connection()
    session = await adapter._manager.connect(conn)

    # Default is a normal session.
    state = await adapter.current(_call_for(str(session.key)))
    assert state["security_context"] == "normal"

    # A privileged login (su --administrative) patches the context.
    await adapter.update(
        Call(
            port="session",
            method="update",
            caller_path="",
            caller_session_key=str(session.key),
        ),
        patch={"security_context": "administrative"},
    )
    state = await adapter.current(_call_for(str(session.key)))
    assert state["security_context"] == "administrative"

    # logout resets the security context to normal.
    await adapter.logout(
        Call(
            port="session",
            method="logout",
            caller_path="",
            caller_session_key=str(session.key),
        )
    )
    state = await adapter.current(_call_for(str(session.key)))
    assert state["security_context"] == "normal"
