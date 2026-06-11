from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Protocol
from y5n.base.runtime import InputContext

if TYPE_CHECKING:
    from y5n.base.projection import Projection
    from y5n.runtime.runtime import Session


class EventStreamOutput:
    """
    High-level projection streaming.

    Responsibilities:
    - lifecycle (begin / abort / finish)
    - block-aware dispatching
    - error safety
    """

    def __init__(
        self,
        on_begin: OnBeginProjection,
        on_emit: OnEmitProjection,
        on_abort: OnAbortProjection,
        on_finish: OnFinishProjection,
    ):
        self.on_begin = on_begin
        self.on_emit = on_emit
        self.on_abort = on_abort
        self.on_finish = on_finish

    async def send_projection(
        self,
        session: Session,
        projection: Projection,
        *,
        ctx: InputContext | None,
        job_id: str = "system",
        mode: str = "replace",
        view_params: dict | None = None,
    ):
        if not projection.id:
            raise RuntimeError("Projection without id.")

        await self.on_begin(
            session=session,
            projection=projection,
            ctx=ctx,
            job_id=job_id,
            reset=(mode == "replace"),
            view_params=view_params,
        )

        try:
            await self.on_emit(
                session=session,
                projection=projection,
            )

        except Exception:
            await self.on_abort(
                session=session,
                projection_id=projection.id,
            )

        else:
            await self.on_finish(
                session=session,
                projection=projection,
            )


# -------------
# --- PORTS ---
# -------------


class OnBeginProjection(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        projection: Projection,
        ctx: InputContext | None,
        job_id: str,
        reset: bool = True,
        view_params: dict | None = None,
    ) -> None: ...


class OnEmitProjection(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        projection: Projection,
    ) -> None: ...


class OnAbortProjection(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        projection_id: str,
    ) -> None: ...


class OnFinishProjection(Protocol):

    async def __call__(
        self,
        *,
        session: Session,
        projection: Projection,
    ) -> None: ...
