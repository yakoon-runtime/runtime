import asyncio
import json

import websockets
from y5n.base.clients import ClientConnection
from y5n.base.projection.wire import deserialize_event
from y5n.base.runtime import Event


class WebSocketClientTransport:

    def __init__(self, url: str):
        self._url = url
        self._websocket = None
        self._receive_task = None

    async def connect(self, on_emit):

        self._websocket = await websockets.connect(self._url)

        async def receive_loop():
            async for msg in self._websocket:
                data = json.loads(msg)

                if data.get("type") == "projection":
                    event = deserialize_event(data["payload"])
                    await on_emit(event)

        async def send_input(event: Event):
            payload = {
                "type": "input",
                "payload": {
                    "raw": str(event.payload),
                    "context": {
                        "origin": getattr(event.context, "origin", None),
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
        if self._receive_task:
            self._receive_task.cancel()
        if self._websocket:
            await self._websocket.close()
        self._websocket = None
        self._receive_task = None
