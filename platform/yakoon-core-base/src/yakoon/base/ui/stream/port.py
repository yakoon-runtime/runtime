from typing import Protocol

from yakoon.base.runtime.sessions import Session
from yakoon.base.ui import ViewSpec

from .stream import OutputStreaming


class OutputStreamService(Protocol):

    async def emit(
        self,
        session: Session,
        view: ViewSpec,
        *,
        override: OutputStreaming | None = None,
    ) -> None: ...
