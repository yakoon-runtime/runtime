from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from y5n.runtime.api.document import DocumentEvent


class IO(Protocol):

    async def view(
        self,
        event: DocumentEvent,
    ) -> None: ...
