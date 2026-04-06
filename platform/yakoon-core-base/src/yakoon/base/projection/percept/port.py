from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from yakoon.base.runtime import InputContext

if TYPE_CHECKING:
    from yakoon.platform.runtime import Session

    from ..model import Projection


class ProjectionDispatcher(Protocol):

    async def begin_projection(
        self,
        session: Session,
        projection: Projection,
        *,
        ctx: InputContext,
        job_id: str,
    ) -> None: ...

    async def emit_projection(
        self,
        session: Session,
        projection: Projection,
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
