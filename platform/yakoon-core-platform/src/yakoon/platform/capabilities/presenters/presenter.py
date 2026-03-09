from __future__ import annotations

from dataclasses import replace
from typing import Any
from uuid import uuid4

from yakoon.base.capabilities.interaction import InteractionService
from yakoon.base.capabilities.presenters import PresentResult
from yakoon.base.rendering import RenderContext, RenderService
from yakoon.base.resources.resource import ResourceRef
from yakoon.base.runtime import Session
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.ui.blocks import Block, TextBlock
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
        self._view_id = f"view.{uuid4().hex}"

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
            view = replace(view, id=self._view_id)

        normalized = self._normalize_blocks(view.blocks)
        view = replace(view, blocks=normalized)

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

    def _normalize_blocks(self, blocks: list[Block]) -> list[Block]:
        """
        Minimal structural normalization before playback.

        Current rules:
          - merge adjacent TextBlocks with equal style
          - drop empty text blocks
        """
        out: list[Block] = []

        for block in blocks:
            if isinstance(block, TextBlock):
                if self._is_empty_text(block):
                    continue

                if (
                    out
                    and isinstance(out[-1], TextBlock)
                    and out[-1].style == block.style
                ):
                    prev = out[-1]
                    merged = replace(prev, text=self._merge_text(prev.text, block.text))
                    out[-1] = merged
                    continue

            out.append(block)

        return out

    def _is_empty_text(self, block: TextBlock) -> bool:
        text = block.text
        if isinstance(text, str):
            return text == ""
        return len(text) == 0

    def _merge_text(
        self, left: str | list[Any], right: str | list[Any]
    ) -> str | list[Any]:
        if isinstance(left, str) and isinstance(right, str):
            if not left:
                return right
            if not right:
                return left
            return f"{left}\n{right}"

        if isinstance(left, list) and isinstance(right, list):
            return [*left, *right]

        return f"{left}{right}"
