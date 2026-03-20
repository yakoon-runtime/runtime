from __future__ import annotations

from typing import Any

from yakoon.base.capabilities.presenters import BlockGroup
from yakoon.base.rendering import RenderContext, RenderService
from yakoon.base.resources import ResourceRef
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

    def group_blocks_by_type(self, view: ViewSpec) -> list[BlockGroup]:

        if view.id is None:
            raise RuntimeError("ViewSpec without id (group_blocks_by_type)")

        groups: list[BlockGroup] = []

        current_blocks = []
        current_type = ""

        view_id = view.id
        for block in view.blocks:

            if not current_type:
                current_type = block.type

            if block.type != current_type:
                groups.append(
                    BlockGroup(
                        view_id,
                        current_type,
                        current_blocks,
                    )
                )
                current_blocks = []
                current_type = block.type

            current_blocks.append(block)

        if current_blocks:
            groups.append(
                BlockGroup(
                    view_id,
                    current_type,
                    current_blocks,
                )
            )

        return groups
