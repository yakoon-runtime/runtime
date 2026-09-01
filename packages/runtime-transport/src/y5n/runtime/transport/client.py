import asyncio
import json

import websockets
from y5n.runtime.api.clients import ClientConnection, SessionNotFound
from y5n.runtime.api.document.wire import deserialize_event
from y5n.runtime.api.flow.patterns.public import FormAction
from y5n.runtime.api.runtime import Event, Routing


class WebSocketClientTransport:

    def __init__(self, url: str, *, exit_on_done: bool = False):
        self._url = url
        self._websocket = None
        self._receive_task = None
        self._on_done = None
        self._exit_on_done = exit_on_done

    def set_on_done(self, callback):
        self._on_done = callback

    async def connect(self, on_emit, session_key: str | None = None):

        # Optional resume request: connection-scoped handshake header.
        # No header means CREATE.
        headers = {"X-Session-Key": session_key} if session_key else None
        self._websocket = await websockets.connect(
            self._url, additional_headers=headers
        )

        async def handle_frame(data) -> bool:
            """Handle one runtime frame; return False to end the loop."""
            if data.get("type") == "document":
                event = deserialize_event(data["payload"])
                await on_emit(event)

            elif data.get("type") == "done":
                if self._on_done:
                    await self._on_done()
                if self._exit_on_done:
                    return False

            return True

        async def receive_loop(stashed):
            try:
                assert self._websocket is not None
                for data in stashed:
                    if not await handle_frame(data):
                        return
                async for msg in self._websocket:
                    if not await handle_frame(json.loads(msg)):
                        break
            finally:
                if self._websocket:
                    await self._websocket.close()
                self._websocket = None

        async def send_input(event: Event):
            ctx = event.context or {}
            payload = event.payload
            msg: dict = {
                "type": "input",
                "payload": {
                    "context": {
                        "origin": getattr(ctx, "origin", None),
                        "echo": getattr(ctx, "echo", None),
                    },
                },
            }

            if isinstance(payload, str):
                msg["payload"]["raw"] = payload
            elif isinstance(payload, FormAction):
                msg["payload"].update(payload.to_wire())
            else:
                msg["payload"]["raw"] = str(payload)

            if event.routing is not Routing.DEFAULT:
                msg["payload"]["__routing__"] = event.routing.name

            await self._websocket.send(json.dumps(msg))

        # Synchronous handshake: decide CREATE/RESUME before the receive
        # task starts, so connect() never returns without a decided
        # session. Frames that raced the handshake (the session is
        # already joined at this point) are stashed and replayed.
        stashed: list[dict] = []
        assigned: str | None = None
        while True:
            data = json.loads(await self._websocket.recv())
            if data.get("type") == "connected":
                assigned = data.get("session_key")
                break
            if data.get("type") == "error":
                await self._websocket.close()
                self._websocket = None
                if data.get("code") == SessionNotFound.code:
                    raise SessionNotFound(
                        data.get("message", "session handshake failed")
                    )
                raise RuntimeError(
                    data.get("message", "session handshake failed")
                )
            stashed.append(data)

        connection = ClientConnection(
            emit=on_emit,
            dispatch=send_input,
        )
        connection.session_key = assigned

        self._receive_task = asyncio.create_task(receive_loop(stashed))

        return connection

    async def close(self):
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None
