from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Protocol

from yakoon.base.runtime import InputContext

if TYPE_CHECKING:
    from yakoon.base.projection import Projection
    from yakoon.platform.runtime import Session


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
    ):
        if not projection.id:
            raise RuntimeError("Projection without id.")

        await self.on_begin(
            session=session,
            projection=projection,
            ctx=ctx,
            job_id=job_id,
        )

        try:
            await self.on_emit(
                session=session,
                projection=projection,
            )

        except Exception:
            # sauber abbrechen (keine halb-fertigen Streams)
            await self.on_abort(
                session=session,
                projection_id=projection.id,
            )
            raise

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
