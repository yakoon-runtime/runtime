import json

from y5n.runtime.api.clients import ClientConnection
from y5n.runtime.api.document.wire import serialize_event
from y5n.runtime.api.flow.patterns.public import FormAction
from y5n.runtime.api.naming import Key
from y5n.runtime.api.runtime import Event, Routing
from y5n.runtime.api.runtime.input.context import InputContext, Origin


class WebSocketServerTransport:

    def __init__(self, host):
        self._host = host

    async def connect(self, websocket):

        # Optional resume request: connection-scoped handshake header.
        # No header means CREATE.
        raw_key = websocket.request.headers.get("X-Session-Key")
        session_key = Key.from_str(raw_key) if raw_key else None

        # Runtime → Client
        async def send(event):
            payload = {
                "type": "document",
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

        try:
            session = await self._host.connect(connection, session_key=session_key)
        except RuntimeError as exc:
            # Resume failed: report it before the connection dies so the
            # client does not have to infer failure from a missing frame.
            await websocket.send(
                json.dumps({"type": "error", "message": str(exc)})
            )
            raise

        # Tell the client which session it is bound to (actual key —
        # assigned on CREATE, requested on RESUME).
        await websocket.send(
            json.dumps({"type": "connected", "session_key": str(session.key)})
        )

        # Send "done" over WS when a flow on this host
        # completes.
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

    origin_str = context.get("origin")
    origin = Origin(origin_str) if origin_str else Origin.HUMAN
    ctx = InputContext(
        origin=origin,
        channel=context.get("channel"),
        echo=payload.get("raw") or "",
    )

    type_hint = payload.get("__type__")

    if type_hint == "FormAction":
        return Event(
            payload=FormAction.from_wire(payload),
            context=ctx,
        )

    routing_name = payload.get("__routing__")
    routing = Routing[routing_name] if routing_name else Routing.DEFAULT
    raw = payload.get("raw") or ""
    return Event.from_raw(data=raw, context=ctx, routing=routing)
