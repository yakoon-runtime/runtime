from __future__ import annotations

from typing import Any

from yakoon.base.rendering import RenderContext, RenderService
from yakoon.base.resources.resource import ResourceRef
from yakoon.base.runtime import Session
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.ui.document import ViewSpec


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

        self._ctx = RenderContext(
            resource=resource,
            lang=session.lang,
        )

    async def view(
        self,
        state: str,
        **data: Any,
    ) -> ViewSpec:
        view = await self._renderer.render_view(self._ctx, state, **data)
        if view.id is None:
            raise RuntimeError(
                "Renderer returned a ViewSpec without id (parser invariant violated)"
            )
        return view
