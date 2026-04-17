import asyncio
import json

from yakoon.base.projection.model.serialize import serialize_event


class WebSocketConnection:

    def __init__(self, websocket):
        self.ws = websocket

    def queue(self, event):
        # direkt senden (kein buffering erstmal)
        asyncio.create_task(self.send(event))

    async def send(self, event):

        # ProjectionEvent → JSON
        await self.ws.send(
            json.dumps(
                {
                    "type": "projection",
                    "payload": serialize_event(event),
                }  # später sauber serialisieren
            )
        )
