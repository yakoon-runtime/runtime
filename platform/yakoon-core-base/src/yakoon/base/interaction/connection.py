# yakoon/platform/interaction/connection.py

import asyncio
from collections.abc import Awaitable, Callable


class ClientConnection:

    def __init__(self, send: Callable[[object], Awaitable[None]], set_flow_control):
        self._send = send
        self._set_flow_control = set_flow_control

    async def send(self, event) -> None:
        await self._send(event)

    def queue(self, event):
        asyncio.create_task(self.send(event))

    def set_flow_control(self, flow):
        self._set_flow_control(flow)
