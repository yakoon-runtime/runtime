from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from yakoon.base.ui import ViewSpec

from .stream import OutputStreaming

if TYPE_CHECKING:
    from yakoon.base.runtime import Session


class OutputStreamService(Protocol):

    async def emit(
        self,
        session: Session,
        view: ViewSpec,
        *,
        override: OutputStreaming | None = None,
    ) -> None: ...
