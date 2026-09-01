"""WebSocket session handshake: transport the session key, decide CREATE
or RESUME before connect() returns, and propagate resume failures without
a CREATE fallback."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from y5n.runtime.api.clients import SessionNotFound
from y5n.runtime.api.naming import Key
from y5n.runtime.transport.client import WebSocketClientTransport
from y5n.runtime.transport.server import WebSocketServerTransport

KEY = "system/session/runtime#test-0"


class FakeClientWebsocket:
    """Scripted client-side websocket: `frames` feed the handshake recv(),
    `live` feeds the post-handshake async iteration."""

    def __init__(self, frames: list[str], live: list[str] | None = None):
        self._frames = list(frames)
        self.live = list(live or [])
        self.sent: list[str] = []
        self.closed = False
        self.headers: dict | None = None

    async def recv(self) -> str:
        if not self._frames:
            raise AssertionError("handshake consumed all scripted frames")
        return self._frames.pop(0)

    def __aiter__(self):
        return self

    async def __anext__(self) -> str:
        if self.live:
            return self.live.pop(0)
        raise StopAsyncIteration

    async def send(self, msg: str) -> None:
        self.sent.append(msg)

    async def close(self) -> None:
        self.closed = True


def _install_client(monkeypatch, frames: list[str], live: list[str] | None = None):
    holder: dict = {}

    async def fake_connect(url, additional_headers=None):
        ws = FakeClientWebsocket(frames, live)
        ws.headers = additional_headers
        holder["ws"] = ws
        return ws

    monkeypatch.setattr(
        "y5n.runtime.transport.client.websockets.connect", fake_connect
    )
    return holder


@pytest.mark.asyncio
async def test_client_handshake_transports_key_and_sets_connection(monkeypatch):
    holder = _install_client(
        monkeypatch,
        frames=[json.dumps({"type": "connected", "session_key": KEY})],
    )
    transport = WebSocketClientTransport("ws://localhost:9100")

    connection = await transport.connect(AsyncMock(), session_key=KEY)

    # resume request traveled as a connection-scoped header
    assert holder["ws"].headers == {"X-Session-Key": KEY}
    # handshake decided before return: key carried on the connection
    assert connection.session_key == KEY
    # receive task is running
    assert transport._receive_task is not None
    await transport.close()


@pytest.mark.asyncio
async def test_client_connect_without_key_sends_no_header(monkeypatch):
    holder = _install_client(
        monkeypatch,
        frames=[json.dumps({"type": "connected", "session_key": KEY})],
    )
    transport = WebSocketClientTransport("ws://localhost:9100")

    connection = await transport.connect(AsyncMock())

    assert holder["ws"].headers is None  # CREATE, no resume request
    assert connection.session_key == KEY
    await transport.close()


@pytest.mark.asyncio
async def test_client_preserves_preconnected_frames(monkeypatch):
    """Frames that raced the handshake (session already joined) are
    replayed through the normal frame handling after connect() returns."""
    on_done = AsyncMock()
    holder = _install_client(
        monkeypatch,
        frames=[
            json.dumps({"type": "done"}),
            json.dumps({"type": "connected", "session_key": KEY}),
        ],
    )
    transport = WebSocketClientTransport("ws://localhost:9100")
    transport.set_on_done(on_done)

    connection = await transport.connect(AsyncMock(), session_key=KEY)
    assert connection.session_key == KEY

    # the stashed frame is replayed by the receive task
    await asyncio.wait_for(transport._receive_task, timeout=1)
    on_done.assert_awaited_once()


@pytest.mark.asyncio
async def test_client_resume_failure_propagates_without_fallback(monkeypatch):
    holder = _install_client(
        monkeypatch,
        frames=[
            json.dumps(
                {
                    "type": "error",
                    "code": "session_not_found",
                    "message": "Session test not found",
                }
            )
        ],
    )
    transport = WebSocketClientTransport("ws://localhost:9100")

    with pytest.raises(SessionNotFound, match="Session test not found") as excinfo:
        await transport.connect(AsyncMock(), session_key=KEY)

    # machine-readable, still compatible with every RuntimeError handler
    assert excinfo.value.code == "session_not_found"
    assert isinstance(excinfo.value, RuntimeError)

    ws = holder["ws"]
    assert ws.closed is True
    assert transport._receive_task is None  # receive task never started
    # no connected frame was sent, no session was created server-side


@pytest.mark.asyncio
async def test_client_generic_error_stays_runtime_error(monkeypatch):
    """An error frame without the session_not_found code must not be
    misread as a lost session."""
    holder = _install_client(
        monkeypatch,
        frames=[json.dumps({"type": "error", "message": "runtime is on fire"})],
    )
    transport = WebSocketClientTransport("ws://localhost:9100")

    with pytest.raises(RuntimeError, match="runtime is on fire") as excinfo:
        await transport.connect(AsyncMock(), session_key=KEY)

    assert not isinstance(excinfo.value, SessionNotFound)
    assert holder["ws"].closed is True


class FakeServerWebsocket:
    def __init__(self, headers: dict | None):
        self.request = SimpleNamespace(headers=headers or {})
        self.sent: list[str] = []

    async def send(self, msg: str) -> None:
        self.sent.append(msg)


class FakeHost:
    """RuntimeManager stand-in for the handshake decision."""

    def __init__(self, fail: str | None = None):
        self.received_session_key: Key | None = None
        self.fail = fail  # None | "generic" | "session_not_found"

    async def connect(self, connection, session_key: Key | None = None):
        self.received_session_key = session_key
        if self.fail == "session_not_found":
            raise SessionNotFound("Session test not found")
        if self.fail == "generic":
            raise RuntimeError("runtime is on fire")
        return SimpleNamespace(key=Key.from_str(KEY))

    def register_session_done(self, session_key, callback) -> None:
        pass

    async def disconnect(self, connection) -> None:
        pass

    async def receive_input(self, connection, event) -> None:
        pass


@pytest.mark.asyncio
async def test_server_resolves_header_to_resume_request():
    host = FakeHost()
    ws = FakeServerWebsocket(headers={"X-Session-Key": KEY})
    transport = WebSocketServerTransport(host)

    await transport.connect(ws)

    assert str(host.received_session_key) == KEY
    types = [json.loads(m)["type"] for m in ws.sent]
    assert types[0] == "connected"
    assert json.loads(ws.sent[0])["session_key"] == KEY


@pytest.mark.asyncio
async def test_server_without_header_creates():
    host = FakeHost()
    ws = FakeServerWebsocket(headers=None)
    transport = WebSocketServerTransport(host)

    await transport.connect(ws)

    assert host.received_session_key is None
    assert json.loads(ws.sent[0])["type"] == "connected"


@pytest.mark.asyncio
async def test_server_reports_resume_failure_with_code():
    host = FakeHost(fail="session_not_found")
    ws = FakeServerWebsocket(headers={"X-Session-Key": KEY})
    transport = WebSocketServerTransport(host)

    with pytest.raises(SessionNotFound, match="Session test not found"):
        await transport.connect(ws)

    # the failure is reported as a machine-readable frame before the
    # connection dies
    error_frames = [json.loads(m) for m in ws.sent]
    assert error_frames[-1] == {
        "type": "error",
        "code": "session_not_found",
        "message": "Session test not found",
    }


@pytest.mark.asyncio
async def test_server_reports_generic_failure_without_code():
    host = FakeHost(fail="generic")
    ws = FakeServerWebsocket(headers={"X-Session-Key": KEY})
    transport = WebSocketServerTransport(host)

    with pytest.raises(RuntimeError, match="runtime is on fire"):
        await transport.connect(ws)

    error_frames = [json.loads(m) for m in ws.sent]
    assert error_frames[-1] == {
        "type": "error",
        "message": "runtime is on fire",
    }
    assert "code" not in error_frames[-1]
