from __future__ import annotations

from dataclasses import replace

from yakoon.base import ports
from yakoon.base.models.stream import OutputStreaming
from yakoon.base.runtime import Session
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.platform.runtime.render.context import RenderContext


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
        self._renderer = services.get(ports.RendererService)
        self._streams = services.get(ports.OutputStreamService)
        self._view_id = view_id

    async def emit(
        self, state: str, *, stream: OutputStreaming | None = None, **data
    ) -> None:
        view = await self._renderer.render_view(self._ctx, state, **data)
        if view.id is None:
            view = replace(view, id=self._view_id)
        await self._streams.emit(self._session, view, override=stream)
