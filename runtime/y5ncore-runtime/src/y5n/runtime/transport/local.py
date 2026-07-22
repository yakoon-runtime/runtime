from __future__ import annotations

from typing import TYPE_CHECKING

from y5n.runtime.engine.clients import ClientConnection

if TYPE_CHECKING:
    from y5n.runtime.machine import RuntimeHost


class LocalTransport:
    """
    Connects a client directly to the host in the same process.
    """

    def __init__(self, host: RuntimeHost):
        self._host = host

    async def connect(self, on_emit):

        async def send_input(event):
            await self._host.receive_input(connection, event)

        connection = ClientConnection(
            emit=on_emit,
            dispatch=send_input,
        )

        await self._host.connect(
            connection,
        )

        return connection
