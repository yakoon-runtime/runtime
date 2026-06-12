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
        await conn.close()
    """

    def __init__(self, url: str):
        self._url = url
        self._transport: WebSocketClientTransport | None = None
        self._connection: ClientConnection | None = None

    async def open(self, on_projection: OnProjection) -> None:
        self._transport = WebSocketClientTransport(self._url)
        self._connection = await self._transport.connect(on_projection)

    async def dispatch(self, event: Event) -> None:
        if self._connection is None:
            raise RuntimeError("Connection not opened")
        await self._connection.dispatch(event)

    async def close(self) -> None:
        if self._transport:
            await self._transport.close()
        self._connection = None
        self._transport = None
