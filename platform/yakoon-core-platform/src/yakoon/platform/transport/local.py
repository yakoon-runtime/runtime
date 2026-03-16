from __future__ import annotations

from typing import TYPE_CHECKING

from yakoon.base.clients import ClientConnection
from yakoon.base.host import Interaction

if TYPE_CHECKING:
    from yakoon.base.ui import IO
    from yakoon.platform.host import RuntimeHost


class LocalTransport:
    """
    Connects a client directly to the host in the same process.
    """

    def __init__(self, host: RuntimeHost):
        self._host = host

    async def connect(self, on_emit, io: IO, interaction: Interaction):

        async def send_input(event):
            await self._host.receive_input(event)

        connection = ClientConnection(
            send=on_emit,
            send_input=send_input,
            io=io,
        )

        await self._host.connect(connection, interaction)

        return connection
