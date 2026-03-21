import asyncio
from collections.abc import Awaitable, Callable


class ClientConnection:

    def __init__(
        self,
        send: Callable[[object], Awaitable[None]],
        send_input: Callable[[object], Awaitable[None]],
    ):
        self._send = send
        self._send_input = send_input

    async def send(self, event) -> None:
        await self._send(event)

    async def send_input(self, event):
        await self._send_input(event)

    def queue(self, event):
        asyncio.create_task(self.send(event))
