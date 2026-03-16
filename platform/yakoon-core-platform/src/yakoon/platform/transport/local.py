# yakoon/platform/transport/local.py

from __future__ import annotations

from collections.abc import Awaitable, Callable

# from yakoon.base.interaction import ClientConnection


class LocalTransport:
    """
    Connects a client directly to the host in the same process.
    """

    def __init__(self, host):
        self._host = host

    async def connect(
        self,
        on_event: Callable[[object], Awaitable[None]],
    ):
        """
        on_event is called whenever the host sends an event to the client.
        """

        async def send(event):
            await on_event(event)

        # connection = ClientConnection(send)

        # runner = await self._host.connect(connection)

        return runner
