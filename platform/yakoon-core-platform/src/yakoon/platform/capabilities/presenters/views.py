from __future__ import annotations

from dataclasses import replace

from yakoon.base.rendering import RenderContext, RenderService
from yakoon.base.runtime import Session
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.ui.stream import OutputStreaming, OutputStreamService


class PresenterViews:

    def __init__(
        self,
        ctx: RenderContext,
        session: Session,
        services: ServiceDirectory,
        view_id: str,
    ):
        self._ctx = ctx
        self._session = session
        self._renderer = services.get(RenderService)
        self._streams = services.get(OutputStreamService)
        self._view_id = view_id

    async def emit(
        self, state: str, *, stream: OutputStreaming | None = None, **data
    ) -> None:
        view = await self._renderer.render_view(self._ctx, state, **data)
        if view.id is None:
            view = replace(view, id=self._view_id)
        await self._streams.emit(self._session, view, override=stream)
