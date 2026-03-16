import asyncio
from collections.abc import Awaitable, Callable

from yakoon.base.ui import IO, FlowControl


class ClientConnection:

    def __init__(
        self,
        send: Callable[[object], Awaitable[None]],
        send_input: Callable[[object], Awaitable[None]],
        io: IO,
    ):
        self._send = send
        self._io = io
        self._send_input = send_input

    async def send(self, event) -> None:
        await self._send(event)

    async def send_input(self, event):
        await self._send_input(event)

    def queue(self, event):
        asyncio.create_task(self.send(event))

    def set_flow_control(self, flow: FlowControl):
        self._io.set_flow_control(flow)
