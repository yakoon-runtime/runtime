from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from y5n.runtime.api.runtime.info import RuntimeInfo
from y5n.runtime.api.runtime.input import Event


class ClientConnection:
    runtime_info: RuntimeInfo | None = None

    def __init__(
        self,
        emit: Callable[[object], Awaitable[None]],
        dispatch: Callable[[Event], Awaitable[None]],
    ):
        self._emit = emit
        self._dispatch = dispatch

    async def emit(self, event) -> None:
        await self._emit(event)

    async def dispatch(self, event):
        await self._dispatch(event)

    def queue(self, event):
        asyncio.create_task(self.emit(event))
