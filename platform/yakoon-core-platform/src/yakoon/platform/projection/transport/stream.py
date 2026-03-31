from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.projection.model import Projection
    from yakoon.platform.runtime import Session

from .dispatcher import EventProjectionDispatcher


class EventStreamOutput:

    def __init__(self):
        self.dispatcher = EventProjectionDispatcher()

    async def send_projection(self, session: Session, projection: Projection):
        if not projection.id:
            raise RuntimeError("View without id.")

        await self.dispatcher.begin_projection(session, projection)

        try:
            for i, block in enumerate(projection.blocks):
                await self.dispatcher.emit_block(
                    session,
                    projection=projection,
                    block=block,
                    suffix=i,
                )
        except Exception:
            await self.dispatcher.abort_projection(session, projection.id)
            raise
        else:
            await self.dispatcher.finish_projection(session, projection)
