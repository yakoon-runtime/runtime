from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from y5n.runtime.api.clients import ClientConnection
from y5n.runtime.api.naming import Key
from y5n.runtime.api.runtime import RuntimeInfo
from y5n.runtime.engine.machine.manager import RuntimeManager
from y5n.runtime.engine.machine.runner import Runner
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData

_COUNTER = 0


def _unique_key() -> Key:
    global _COUNTER
    _COUNTER += 1
    return Key.from_parts("test", "session", "runtime", f"auto{_COUNTER}")


def _fake_connection() -> ClientConnection:
    return ClientConnection(
        emit=AsyncMock(),
        dispatch=AsyncMock(),
    )


@pytest.fixture
async def manager():
    manager = RuntimeManager(
        on_schedule=AsyncMock(),
        on_get_session=AsyncMock(
            side_effect=lambda: Session(
                key=_unique_key(),
                data=SessionData(),
            )
        ),
        on_resume_session=AsyncMock(
            side_effect=RuntimeError("Session not found")
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
    return manager


@pytest.mark.asyncio
async def test_connect_creates_home_session(manager: RuntimeManager):
    conn = _fake_connection()
    session = await manager.connect(conn)

    rows = manager.list_sessions()
    assert len(rows) == 1
    assert rows[0]["key"] == str(session.key)
    assert rows[0]["homes"] == 1
    assert rows[0]["clients"] == 1
    assert rows[0]["flows"] == 0


@pytest.mark.asyncio
async def test_connect_two_connections_two_home_sessions(manager: RuntimeManager):
    c1 = _fake_connection()
    c2 = _fake_connection()
    s1 = await manager.connect(c1)
    s2 = await manager.connect(c2)

    assert str(s1.key) != str(s2.key)

    rows = manager.list_sessions()
    assert len(rows) == 2
    rows_by_key = {r["key"]: r for r in rows}
    assert rows_by_key[str(s1.key)]["homes"] == 1
    assert rows_by_key[str(s2.key)]["homes"] == 1


@pytest.mark.asyncio
async def test_attach_target_becomes_active(manager: RuntimeManager):
    c1 = _fake_connection()
    s1 = await manager.connect(c1)

    c2 = _fake_connection()
    s2 = await manager.connect(c2)

    await manager.attach_session(s1, str(s2.key))

    rows = manager.list_sessions()
    rows_by_key = {r["key"]: r for r in rows}

    # s1 is subscribed to both, active = s2
    assert rows_by_key[str(s1.key)]["clients"] == 1
    assert rows_by_key[str(s2.key)]["clients"] == 2


@pytest.mark.asyncio
async def test_attach_does_not_change_home(manager: RuntimeManager):
    c1 = _fake_connection()
    s1 = await manager.connect(c1)

    c2 = _fake_connection()
    s2 = await manager.connect(c2)

    old_homes = {r["key"]: r["homes"] for r in manager.list_sessions()}

    await manager.attach_session(s1, str(s2.key))

    new_homes = {r["key"]: r["homes"] for r in manager.list_sessions()}
    assert new_homes == old_homes


@pytest.mark.asyncio
async def test_detach_returns_to_home(manager: RuntimeManager):
    c1 = _fake_connection()
    s1 = await manager.connect(c1)

    c2 = _fake_connection()
    s2 = await manager.connect(c2)

    await manager.attach_session(s1, str(s2.key))

    await manager.detach_session(s2)

    rows = manager.list_sessions()
    rows_by_key = {r["key"]: r for r in rows}

    # s1 should be back to 1 client (only c1), s2 to 1 client (only c2)
    assert rows_by_key[str(s1.key)]["clients"] == 1
    assert rows_by_key[str(s2.key)]["clients"] == 1


@pytest.mark.asyncio
async def test_detach_on_home_is_noop(manager: RuntimeManager):
    conn = _fake_connection()
    session = await manager.connect(conn)

    # detaching from home should not change anything
    await manager.detach_session(session)

    rows = manager.list_sessions()
    assert len(rows) == 1
    assert rows[0]["clients"] == 1
    assert rows[0]["homes"] == 1


@pytest.mark.asyncio
async def test_shared_workspace_two_clients(manager: RuntimeManager):
    c1 = _fake_connection()
    s1 = await manager.connect(c1)

    c2 = _fake_connection()
    s2 = await manager.connect(c2)

    # c1 attaches to s2 — both observe s2
    await manager.attach_session(s1, str(s2.key))

    rows = manager.list_sessions()
    rows_by_key = {r["key"]: r for r in rows}
    assert rows_by_key[str(s2.key)]["clients"] == 2


@pytest.mark.asyncio
async def test_cleanup_no_subscribers_no_flows(manager: RuntimeManager):
    conn = _fake_connection()
    await manager.connect(conn)

    await manager.disconnect(conn)

    rows = manager.list_sessions()
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_flow_complete_triggers_cleanup(manager: RuntimeManager):
    conn = _fake_connection()
    session = await manager.connect(conn)
    runner = manager._sessions[session.key]

    # A flow is running
    flow = MagicMock()
    flow.id = "flow-1"
    runner.session.add_flow(flow)

    await manager.disconnect(conn)

    # Session survives — flow still running
    assert len(manager.list_sessions()) == 1

    # Simulate Stop.on_enter: flow removed from session
    runner.session.del_flow(flow)

    # Host notified: flow is done
    await manager.flow_complete(flow, session)

    # No clients, no flows → cleaned up
    assert len(manager.list_sessions()) == 0


@pytest.mark.asyncio
async def test_receive_input_always_has_active_session(manager: RuntimeManager):
    conn = _fake_connection()
    await manager.connect(conn)

    event = AsyncMock()
    # must not raise
    await manager.receive_input(conn, event)


@pytest.mark.asyncio
async def test_receive_input_after_detach_still_works(manager: RuntimeManager):
    c1 = _fake_connection()
    s1 = await manager.connect(c1)

    c2 = _fake_connection()
    s2 = await manager.connect(c2)

    await manager.attach_session(s1, str(s2.key))
    await manager.detach_session(s2)

    # after detach, c1 is back on s1 — receive_input must not raise
    event = AsyncMock()
    await manager.receive_input(c1, event)


@pytest.mark.asyncio
async def test_disconnect_cleans_home(manager: RuntimeManager):
    conn = _fake_connection()
    await manager.connect(conn)

    await manager.disconnect(conn)

    rows = manager.list_sessions()
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_disconnect_with_active_subscription(manager: RuntimeManager):
    c1 = _fake_connection()
    s1 = await manager.connect(c1)

    c2 = _fake_connection()
    s2 = await manager.connect(c2)

    await manager.attach_session(s1, str(s2.key))

    # disconnect c1 — should leave both s1 and s2
    await manager.disconnect(c1)

    rows = manager.list_sessions()
    rows_by_key = {r["key"]: r for r in rows}
    assert rows_by_key[str(s2.key)]["clients"] == 1  # only c2 remains on s2
