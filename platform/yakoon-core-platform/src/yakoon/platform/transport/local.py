from collections.abc import Awaitable, Callable

from yakoon.base.interaction import ClientConnection


class LocalTransport:
    """
    Connects a client directly to the host in the same process.
    """

    def __init__(self, host):
        self._host = host

    async def connect(
        self,
        on_event: Callable[[object], Awaitable[None]],
        set_flow_control,
    ):
        """
        Connect client to host in same process.
        """

        connection = ClientConnection(
            send=on_event,
            set_flow_control=set_flow_control,
        )

        await self._host.connect(connection)

        return connection
