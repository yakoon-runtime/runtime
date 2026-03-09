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
from yakoon.base.ui import Block, FieldsBlock, ViewSpec
from yakoon.base.ui.stream import OutputStreaming


class DefaultPresenter:
    """
    Unified presenter.

    The presenter renders one state into a single UI document and then walks
    through the document block-by-block.

    Behavior:
      - passive blocks are emitted immediately
      - FieldsBlock(form) is emitted, but does not implicitly wait
      - FieldsBlock(prompt) is emitted, then delegated to InputService, then
        presentation continues with the following blocks

    Important:
    This version already implements the new *resume after prompt* semantics.
    It currently emits accumulated document snapshots via session.emit(...).
    The lower-level streaming/chunking service can later be made resumable
    underneath this presenter without changing command code again.
    """

    def __init__(
        self,
        resource: ResourceRef,
        session: Session,
        services: ServiceDirectory,
    ) -> None:
        self._session = session
        self._services = services
        self._renderer = services.get(RenderService)
        self._inputs = services.get(InteractionService)
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
        rendered = await self._renderer.render_view(self._ctx, state, **data)

        if rendered.id is None:
            rendered = replace(rendered, id=self._view_id)

        # Reserved for the next step when the resumable output streamer is adapted.
        _stream = stream

        emitted_blocks: list[Block] = []
        values: dict[str, Any] = {}
        aliases: dict[str, str] = {}
        order: list[str] = []

        for idx, raw_block in enumerate(rendered.blocks):
            block = self._ensure_block_id(rendered.id or self._view_id, idx, raw_block)
            emitted_blocks.append(block)

            await self._emit_snapshot(rendered, emitted_blocks)

            if not isinstance(block, FieldsBlock):
                continue

            if block.input_mode == "form":
                # visible, but no implicit wait
                continue

            if block.input_mode != "prompt":
                continue

            result = await self._inputs.run_fields(
                self._session,
                view_id=rendered.id or self._view_id,
                block=block,
            )
            self._merge_result(
                result=result,
                values=values,
                aliases=aliases,
                order=order,
            )

        if not values:
            return None

        return PresentResult(values, aliases, order)

    async def _emit_snapshot(
        self,
        rendered: ViewSpec,
        emitted_blocks: list[Block],
    ) -> None:
        snapshot = replace(
            rendered,
            blocks=list(emitted_blocks),
        )
        await self._session.emit(snapshot)

    def _ensure_block_id(
        self,
        view_id: str,
        index: int,
        block: Block,
    ) -> Block:
        bid = getattr(block, "id", None)
        if isinstance(bid, str) and bid:
            return block
        return replace(block, id=f"{view_id}:b{index}")

    def _merge_result(
        self,
        *,
        result: PresentResult,
        values: dict[str, Any],
        aliases: dict[str, str],
        order: list[str],
    ) -> None:
        for key, value in result.dict().items():
            values[key] = value

        for alias, var in result._aliases.items():
            aliases[alias] = var

        for key in result._order:
            if key not in order:
                order.append(key)
