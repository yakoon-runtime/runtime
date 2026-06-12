from __future__ import annotations

from collections.abc import Awaitable, Callable

from y5n.base.clients import ClientConnection
from y5n.base.runtime import Event
from y5ntrans.websocket.client import WebSocketClientTransport

OnProjection = Callable[[object], Awaitable[None]]


class RuntimeConnection:
    """A connection to a remote Runtime.

    Usage:
        conn = RuntimeConnection(url="ws://localhost:9101")
        await conn.open(on_projection=router)
        await conn.dispatch(Event(payload="hello"))
        # Connection auto-closes when remote sends "done".
    """

    def __init__(self, url: str):
        self._url = url
        self._transport: WebSocketClientTransport | None = None
        self._connection: ClientConnection | None = None

    async def open(self, on_projection: OnProjection) -> None:
        self._transport = WebSocketClientTransport(self._url, exit_on_done=True)
        self._transport.set_on_done(self.close)
        self._connection = await self._transport.connect(on_projection)

    def set_on_done(self, callback: Callable[[], Awaitable[None]]) -> None:
        if self._transport:
            self._transport.set_on_done(callback)

    async def dispatch(self, event: Event) -> None:
        if self._connection is None:
            raise RuntimeError("Connection not opened")
        await self._connection.dispatch(event)

    async def close(self) -> None:
        if self._transport:
            await self._transport.close()
        self._connection = None
        self._transport = None
