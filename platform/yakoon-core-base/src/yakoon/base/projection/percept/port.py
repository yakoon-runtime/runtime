from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from yakoon.platform.runtime import Session

    from ..model import Block, Projection


class ProjectionDispatcher(Protocol):

    async def begin_projection(
        self,
        session: Session,
        projection: Projection,
    ) -> None: ...

    async def emit_block(
        self,
        session: Session,
        *,
        projection: Projection,
        block: Block,
        parent_id: str | None = None,
        suffix: str | int = 0,
    ) -> None: ...

    async def abort_projection(
        self,
        session: Session,
        projection_id: str,
    ) -> None: ...

    async def finish_projection(
        self,
        session: Session,
        projection: Projection,
    ) -> None: ...
