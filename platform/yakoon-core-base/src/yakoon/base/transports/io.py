from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from yakoon.base.ui import ViewEvent


class IO(Protocol):

    async def view(
        self,
        event: ViewEvent,
    ) -> None: ...
