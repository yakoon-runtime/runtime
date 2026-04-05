from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.projection.model import Projection
    from yakoon.platform.runtime import Session

from .dispatcher import EventProjectionDispatcher


class EventStreamOutput:
    """
    High-level projection streaming.

    Responsibilities:
    - lifecycle (begin / abort / finish)
    - block-aware dispatching
    - error safety
    """

    def __init__(self):
        self.dispatcher = EventProjectionDispatcher()

    async def send_projection(
        self,
        session: Session,
        projection: Projection,
        *,
        job_id: str = "system",
    ):
        if not projection.id:
            raise RuntimeError("Projection without id.")

        await self.dispatcher.begin_projection(
            session,
            projection,
            job_id=job_id,
        )

        try:
            await self.dispatcher.emit_projection(
                session,
                projection,
            )

        except Exception:
            # sauber abbrechen (keine halb-fertigen Streams)
            await self.dispatcher.abort_projection(
                session,
                projection.id,
            )
            raise

        else:
            await self.dispatcher.finish_projection(
                session,
                projection,
            )
