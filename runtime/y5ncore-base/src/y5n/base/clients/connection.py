import asyncio
from collections.abc import Awaitable, Callable

from y5n.base.runtime.input import InputEvent


class ClientConnection:

    def __init__(
        self,
        emit: Callable[[object], Awaitable[None]],
        dispatch: Callable[[InputEvent], Awaitable[None]],
    ):
        self._emit = emit
        self._dispatch = dispatch

    async def emit(self, event) -> None:
        await self._emit(event)

    async def dispatch(self, event):
        await self._dispatch(event)

    def queue(self, event):
        asyncio.create_task(self.emit(event))
