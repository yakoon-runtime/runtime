import asyncio
import json

import websockets
from y5n.base.clients import ClientConnection
from y5n.base.projection.wire import deserialize_event
from y5n.base.runtime import InputEvent


class WebSocketClientTransport:

    def __init__(self, url: str):
        self._url = url

    async def connect(self, on_emit):

        websocket = await websockets.connect(self._url)

        # ------------------------
        # Runtime → Client
        # ------------------------
        async def receive_loop():
            async for msg in websocket:
                data = json.loads(msg)

                if data.get("type") == "projection":
                    event = deserialize_event(data["payload"])
                    await on_emit(event)

        # ------------------------
        # Client → Server
        # ------------------------
        async def send_input(event: InputEvent):
            payload = {
                "type": "input",
                "payload": {
                    "raw": event.command,
                    "context": {
                        "origin": getattr(event.context, "origin", None),
                    },
                },
            }
            await websocket.send(json.dumps(payload))

        connection = ClientConnection(
            emit=on_emit,
            dispatch=send_input,
        )

        asyncio.create_task(receive_loop())

        return connection
