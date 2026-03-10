from __future__ import annotations

from typing import Any

from yakoon.base.capabilities.interaction import InteractionService
from yakoon.base.capabilities.presenters import PresentResult
from yakoon.base.rendering import RenderContext, RenderService
from yakoon.base.resources.resource import ResourceRef
from yakoon.base.runtime import Session
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.ui.stream import OutputStreaming


class DefaultPresenter:
    """
    Unified presenter.

    Responsibilities:
      - render a state into a UI document
      - normalize the resulting block sequence
      - delegate actual playback to InteractionService
    """

    def __init__(
        self,
        resource: ResourceRef,
        session: Session,
        services: ServiceDirectory,
    ) -> None:
        self._session = session
        self._renderer = services.get(RenderService)
        self._interaction = services.get(InteractionService)

        self._ctx = RenderContext(
            resource=resource,
            lang=session.lang,
        )

    async def present(
        self,
        state: str,
        *,
        stream: OutputStreaming | None = None,
        **data: Any,
    ) -> PresentResult | None:

        view = await self._renderer.render_view(self._ctx, state, **data)
        if view.id is None:
            raise RuntimeError(
                "Renderer returned a ViewSpec without id (parser invariant violated)"
            )

        return await self._interaction.play_view(
            self._session,
            view=view,
            stream=stream,
        )

    async def require_present(
        self,
        state: str,
        *,
        stream: OutputStreaming | None = None,
        **data: Any,
    ) -> PresentResult:
        result = await self.present(state, stream=stream, **data)
        if result is None:
            raise RuntimeError(f"Presenter state {state!r} returned no result")
        return result

    async def require_first(
        self,
        state: str,
        *,
        stream: OutputStreaming | None = None,
        **data: Any,
    ) -> Any:
        result = await self.require_present(state, stream=stream, **data)
        return result.first()
