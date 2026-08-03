from __future__ import annotations

from typing import TYPE_CHECKING

from y5n.runtime.api.clients import ClientConnection

if TYPE_CHECKING:
    from y5n.runtime.engine.machine import RuntimeManager


class LocalTransport:
    """
    Connects a client directly to the runtime manager in the same process.
    """

    def __init__(self, manager: RuntimeManager):
        self._manager = manager

    async def connect(self, on_emit):

        async def send_input(event):
            await self._manager.receive_input(connection, event)

        connection = ClientConnection(
            emit=on_emit,
            dispatch=send_input,
        )

        await self._manager.connect(
            connection,
        )

        return connection
