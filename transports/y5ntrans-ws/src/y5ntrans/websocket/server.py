import json

from y5n.base.clients import ClientConnection
from y5n.base.projection.wire import serialize_event
from y5n.base.runtime import Event
from y5n.base.runtime.input.context import InputContext


class WebSocketServerTransport:

    def __init__(self, host):
        self._host = host

    async def connect(self, websocket):

        # Runtime → Client
        async def send(event):
            payload = {
                "type": "projection",
                "payload": serialize_event(event),
            }
            await websocket.send(json.dumps(payload))

        # Client → Runtime
        async def send_input(event):
            await self._host.receive_input(connection, event)

        connection = ClientConnection(
            emit=send,
            dispatch=send_input,
        )

        session = await self._host.connect(connection)

        # Sende "done" über WS wenn ein Flow auf diesem Host
        # komplettiert wird.
        async def session_done():
            await websocket.send(json.dumps({"type": "done"}))

        self._host.register_session_done(str(session.key), session_done)

        # RECEIVE LOOP
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
                        await connection.dispatch(event)

            finally:
                await self._host.disconnect(connection)

        return connection, receive_loop


def map_to_input_event(data):

    payload = data.get("payload", {})
    context = payload.get("context") or {}

    raw = payload.get("raw") or ""

    return Event.from_raw(
        data=raw,
        context=InputContext(
            origin=context.get("origin"),
            echo=raw,
        ),
    )
