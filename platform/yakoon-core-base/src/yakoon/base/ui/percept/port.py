from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from yakoon.platform.runtime import Session

    from .. import Block, View


class ViewDispatcher(Protocol):

    async def begin_view(
        self,
        session: Session,
        view: View,
    ) -> None: ...

    async def emit_block(
        self,
        session: Session,
        *,
        view: View,
        block: Block,
        parent_id: str | None = None,
        suffix: str | int = 0,
    ) -> None: ...

    async def flush_view(
        self,
        view_id: str,
    ) -> None: ...

    async def abort_view(
        self,
        session: Session,
        view_id: str,
    ) -> None: ...

    async def finish_view(
        self,
        session: Session,
        view: View,
    ) -> None: ...
