import asyncio
import json

import websockets

from yakoon.base.projection.model.deserialize import apply_projection


async def test():
    async with websockets.connect("ws://localhost:8765") as ws:
        await ws.send(json.dumps({"type": "connect"}))

        await ws.send(json.dumps({"type": "ping"}))
        msg = await ws.recv()
        print(msg)


async def send_man():
    async with websockets.connect("ws://localhost:8765") as ws:
        await ws.send(json.dumps({"type": "connect"}))

        await ws.send(
            json.dumps(
                {"type": "input", "channel": "command", "payload": {"text": "man"}}
            )
        )

        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            if data["type"] == "projection":
                apply_projection(data["payload"])


asyncio.run(send_man())
