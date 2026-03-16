from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from yakoon.base.clients import ClientConnection
    from yakoon.base.host import Interaction
    from yakoon.base.ui import IO


class Transport(Protocol):

    async def connect(
        self, on_emit, io: IO, interaction: Interaction
    ) -> ClientConnection: ...
