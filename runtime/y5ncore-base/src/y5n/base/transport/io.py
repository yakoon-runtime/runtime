from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from y5n.base.projection import ProjectionEvent


class IO(Protocol):

    async def view(
        self,
        event: ProjectionEvent,
    ) -> None: ...
