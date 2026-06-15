import asyncio
import json

import websockets
from y5n.base.clients import ClientConnection
from y5n.base.projection.wire import deserialize_event
from y5n.base.runtime import Event


class WebSocketClientTransport:

    def __init__(self, url: str, *, exit_on_done: bool = False):
        self._url = url
        self._websocket = None
        self._receive_task = None
        self._on_done = None
        self._exit_on_done = exit_on_done

    def set_on_done(self, callback):
        self._on_done = callback

    async def connect(self, on_emit):

        self._websocket = await websockets.connect(self._url)

        async def receive_loop():
            try:
                async for msg in self._websocket:
                    data = json.loads(msg)

                    if data.get("type") == "projection":
                        event = deserialize_event(data["payload"])
                        await on_emit(event)

                    elif data.get("type") == "done":
                        if self._on_done:
                            await self._on_done()
                        if self._exit_on_done:
                            break
            finally:
                if self._websocket:
                    await self._websocket.close()
                self._websocket = None

        async def send_input(event: Event):
            ctx = event.context or {}
            payload = {
                "type": "input",
                "payload": {
                    "raw": str(event.payload),
                    "context": {
                        "origin": getattr(ctx, "origin", None),
                        "echo": getattr(ctx, "echo", None),
                    },
                },
            }
            await self._websocket.send(json.dumps(payload))

        connection = ClientConnection(
            emit=on_emit,
            dispatch=send_input,
        )

        self._receive_task = asyncio.create_task(receive_loop())

        return connection

    async def close(self):
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None
