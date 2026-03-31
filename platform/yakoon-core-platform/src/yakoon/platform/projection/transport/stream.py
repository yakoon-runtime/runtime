from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.projection.view import View
    from yakoon.platform.runtime import Session

from .dispatcher import DefaultViewDispatcher


class DefaultOutputStream:

    def __init__(self):
        self.dispatcher = DefaultViewDispatcher()

    async def send_view(self, session: Session, view: View):
        if not view.id:
            raise RuntimeError("View without id.")

        await self.dispatcher.begin_view(session, view)

        try:
            for i, block in enumerate(view.blocks):
                await self.dispatcher.emit_block(
                    session,
                    view=view,
                    block=block,
                    suffix=i,
                )
        except Exception:
            await self.dispatcher.abort_view(session, view.id)
            raise
        else:
            await self.dispatcher.finish_view(session, view)
