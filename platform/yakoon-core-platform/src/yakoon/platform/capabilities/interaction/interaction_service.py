from __future__ import annotations

from dataclasses import replace
from typing import Any

from yakoon.base.capabilities.interaction import (
    DialogCancelled,
    PolicyService,
)
from yakoon.base.capabilities.presenters import PresentResult
from yakoon.base.runtime import Session
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.ui import (
    Field,
    FieldsBlock,
    OutputStreaming,
    OutputStreamService,
    View,
    v_error_system,
)


class ConsoleInteractionService:

    def __init__(self, services: ServiceDirectory) -> None:
        self._services = services
        self._policy = services.get(PolicyService)
        self._stream_service: OutputStreamService | None = None

    @property
    def streams(self) -> OutputStreamService:
        if self._stream_service is None:
            self._stream_service = self._services.get(OutputStreamService)
        return self._stream_service

    async def play_view(
        self,
        session: Session,
        *,
        view: View,
        stream: OutputStreaming | None = None,
    ) -> PresentResult | None:

        values: dict[str, Any] = {}
        aliases: dict[str, str] = {}
        order: list[str] = []

        if view.id is None:
            raise RuntimeError("View.id is required for streaming but was None")

        await self.streams.begin_view(session, view, override=stream)
        try:

            for index, block in enumerate(view.blocks):
                if isinstance(block, FieldsBlock) and block.input_mode == "prompt":

                    # hard flush-border before input
                    await self.streams.flush_view(view.id)

                    result = await self.run_fields(
                        session,
                        view_id=view.id,
                        block=block,
                    )

                    # CANCEL SOFORT PROPAGIEREN
                    if result.cancelled:
                        return result

                    self._merge_result(
                        result=result,
                        values=values,
                        aliases=aliases,
                        order=order,
                    )

                    continue

                await self.streams.emit_block(
                    session,
                    view=view,
                    block=block,
                    override=stream,
                    suffix=index,
                )

        except Exception:
            await self.streams.abort_view(session, view.id)
            raise
        else:
            await self.streams.finish_view(session, view, override=stream)

        if not values:
            return None

        return PresentResult(values, aliases, order)

    async def run_fields(
        self,
        session: Session,
        *,
        view_id: str,
        block: FieldsBlock,
    ) -> PresentResult:

        if not block.fields:
            raise TypeError("FieldsBlock.fields must be a non-empty list")

        meta = block.meta or {}

        aliases = meta.get("aliases") or {}
        if not isinstance(aliases, dict):
            aliases = {}

        order = meta.get("order") or self._field_order(block)
        if not isinstance(order, list):
            order = self._field_order(block)

        input_mode = block.input_mode or "prompt"

        try:

            if input_mode == "form":
                out = await self._ask_batch(session, view_id, block, order)
            else:
                out = await self._ask_stepwise(session, view_id, block, order)

        except DialogCancelled:
            return PresentResult.create_cancelled()

        return PresentResult(out, aliases, order)

    def _view_for_block(self, view_id: str, block: FieldsBlock) -> View:
        return View(id=view_id, header=None, blocks=[block])

    def _field_map(self, block: FieldsBlock) -> dict[str, Field]:
        out: dict[str, Field] = {}
        for fd in block.fields:
            if fd.var:
                out[fd.var] = fd
        return out

    def _field_order(self, block: FieldsBlock) -> list[str]:
        return [fd.var for fd in block.fields if fd.var]

    def _with_only_field_block(self, block: FieldsBlock, key: str) -> FieldsBlock:
        only = [fd for fd in block.fields if fd.var == key]
        if not only:
            return block
        return replace(block, fields=only, input_mode="prompt")

    async def _emit_errors(
        self,
        session: Session,
        errors: dict[str, list[str]],
    ) -> None:

        for key, msgs in errors.items():
            for msg in msgs:
                if key == "form":
                    await session.emit(v_error_system(msg, error_kind="validation"))
                else:
                    await session.emit(
                        v_error_system(f"{key}: {msg}", error_kind="validation")
                    )

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
