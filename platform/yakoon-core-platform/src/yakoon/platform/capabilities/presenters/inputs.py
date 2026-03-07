from __future__ import annotations

from dataclasses import replace

from yakoon.base import ports
from yakoon.base.capabilities.interaction import InputService
from yakoon.base.capabilities.presenters import PromptResult
from yakoon.base.runtime import Session
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.ui import ViewSpec
from yakoon.platform.runtime.render.context import RenderContext


class PresenterInputs:

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
        self._inputs = services.get(InputService)
        self._view_id = view_id

    async def ask(self, state: str, **data) -> PromptResult:
        view = await self._renderer.render_view(self._ctx, state, **data)
        if view.id is None:
            view = replace(view, id=self._view_id)
        await self._session.emit(view)
        result = await self._inputs.ask_view(self._session, view)
        await self.close()
        return result

    async def close(self):
        await self._session.emit(
            ViewSpec(
                kind="view",
                id=self._view_id,
                mode="replace",
                input=None,
                output=None,
            )
        )
