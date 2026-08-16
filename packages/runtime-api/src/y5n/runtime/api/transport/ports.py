from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from y5n.runtime.api.clients import ClientConnection


class Transport(Protocol):

    async def connect(self, on_emit) -> ClientConnection: ...
