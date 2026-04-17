import json

from yakoon.base.clients import ClientConnection
from yakoon.base.projection.model.serialize import serialize_event
from yakoon.base.runtime import InputEvent
from yakoon.base.runtime.input.context import InputContext


class WebSocketTransport:

    def __init__(self, host):
        self._host = host

    async def connect(self, websocket):

        # ------------------------
        # Runtime → Client
        # ------------------------
        async def send(event):
            payload = {
                "type": "projection",
                "payload": serialize_event(event),
            }
            await websocket.send(json.dumps(payload))

        # ------------------------
        # Client → Runtime
        # ------------------------
        async def send_input(event):
            await self._host.receive_input(connection, event)

        connection = ClientConnection(
            send=send,
            send_input=send_input,
        )

        # Runtime verbinden
        await self._host.connect(connection)

        # ------------------------
        # RECEIVE LOOP (WICHTIG)
        # ------------------------
        async def receive_loop():
            try:
                async for msg in websocket:
                    data = json.loads(msg)

                    # ping / pong
                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                        continue

                    if data.get("type") == "input":
                        event = map_to_input_event(data)
                        await connection.send_input(event)

            finally:
                await self._host.disconnect(connection)

        return connection, receive_loop


def map_to_input_event(data):

    payload = data.get("payload", {})
    context = payload.get("context") or {}

    return InputEvent.from_raw(
        raw=payload.get("raw"),
        context=InputContext(
            origin=context.get("origin"),
        ),
    )
