from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from yakoon.base.ui import Block, ViewSpec

from .stream import EffectiveStreaming, OutputStreaming, OutputStreamPolicy

if TYPE_CHECKING:
    from yakoon.base.runtime import Session


class OutputStreamService(Protocol):

    def effective(
        self,
        base: OutputStreamPolicy,
        override: OutputStreaming | None,
    ) -> EffectiveStreaming: ...

    async def begin_view(
        self,
        session: Session,
        view: ViewSpec,
        *,
        override: OutputStreaming | None = None,
    ) -> None: ...

    async def emit_block(
        self,
        session: Session,
        *,
        view: ViewSpec,
        block: Block,
        override: OutputStreaming | None = None,
        parent_id: str | None = None,
        suffix: str | int = 0,
    ) -> None: ...

    async def abort_view(
        self,
        session: Session,
        view_id: str,
    ) -> None: ...

    async def finish_view(
        self,
        session: Session,
        view: ViewSpec,
        *,
        override: OutputStreaming | None = None,
    ) -> None: ...
