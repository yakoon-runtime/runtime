from __future__ import annotations

from dataclasses import replace
from typing import Any

from yakoon.base.capabilities.interaction import DialogService, PolicyService
from yakoon.base.capabilities.presenters import PresentResult
from yakoon.base.runtime import Session
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.ui import (
    FieldsBlock,
    OutputStreaming,
    OutputStreamService,
    ViewFieldDef,
    ViewSpec,
    v_error,
)
from yakoon.platform.settings import settings


class DefaultInteractionService:
    def __init__(self, services: ServiceDirectory) -> None:
        self._dialogs = services.get(DialogService)
        self._policy = services.get(PolicyService)
        self._services = services
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
        view: ViewSpec,
        stream: OutputStreaming | None = None,
    ) -> PresentResult | None:
        values: dict[str, Any] = {}
        aliases: dict[str, str] = {}
        order: list[str] = []

        if stream is not None:
            await self.streams.begin_view(session, view, override=stream)
        else:
            await session.emit(replace(view, blocks=[]))

        try:
            for index, block in enumerate(view.blocks):
                if isinstance(block, FieldsBlock) and block.input_mode == "prompt":
                    result = await self.run_fields(
                        session,
                        view_id=view.id or "",
                        block=block,
                        stream=stream,
                    )
                    self._merge_result(
                        result=result,
                        values=values,
                        aliases=aliases,
                        order=order,
                    )
                    continue

                if stream is not None:
                    await self.streams.emit_block(
                        session,
                        view=view,
                        block=block,
                        override=stream,
                        suffix=index,
                    )
                else:
                    snapshot = replace(
                        view,
                        header=None,
                        blocks=[block],
                    )
                    await session.emit(snapshot)
        finally:
            if stream is not None:
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
        stream: OutputStreaming | None = None,
    ) -> PresentResult:
        if not block.fields:
            raise TypeError("FieldsBlock.fields must be a non-empty list")

        meta = block.meta or {}
        aliases = meta.get("aliases") or {}
        order = meta.get("order") or self._field_order(block)

        if not isinstance(aliases, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in aliases.items()
        ):
            aliases = {}

        if not isinstance(order, list) or not all(isinstance(x, str) for x in order):
            order = self._field_order(block)

        input_mode = block.input_mode or "prompt"
        if input_mode not in ("prompt", "form"):
            input_mode = "prompt"

        if input_mode == "form":
            out = await self._ask_batch(session, view_id, block, order)
        else:
            out = await self._ask_stepwise(session, view_id, block, order)

        return PresentResult(out, aliases, order)

    async def _ask_batch(
        self,
        session: Session,
        view_id: str,
        block: FieldsBlock,
        order: list[str],
    ) -> dict[str, object]:
        view = self._view_for_block(view_id, block)

        while True:
            raw = await self._dialogs.wait_view(
                session,
                view=view,
                timeout=settings.network.prompt_timed_out,
            )

            out, errors = await self._validate_all(block, raw, order)

            unknown = set(raw.keys()) - set(self._field_map(block).keys())
            if unknown:
                errors.setdefault("form", []).append(
                    f"Unknown fields: {sorted(unknown)}"
                )

            if not errors:
                return out

            await self._emit_errors(session, errors)

    async def _ask_stepwise(
        self,
        session: Session,
        view_id: str,
        block: FieldsBlock,
        order: list[str],
    ) -> dict[str, object]:
        fields_def = self._field_map(block)
        out: dict[str, object] = {}

        for key in order:
            fd = fields_def.get(key)
            if fd is None:
                continue

            while True:
                step_block = self._with_only_field_block(block, key)
                step_view = self._view_for_block(view_id, step_block)

                raw = await self._dialogs.wait_view(
                    session,
                    view=step_view,
                    timeout=settings.network.prompt_timed_out,
                )

                partial_out, errors = await self._validate_all(
                    step_block,
                    raw,
                    order=[key],
                )

                unknown = set(raw.keys()) - {key}
                if unknown:
                    errors.setdefault("form", []).append(
                        f"Unknown fields: {sorted(unknown)}"
                    )

                if errors:
                    await self._emit_errors(session, errors)
                    continue

                if key in partial_out:
                    out[key] = partial_out[key]
                break

        return out

    def _view_for_block(self, view_id: str, block: FieldsBlock) -> ViewSpec:
        return ViewSpec(
            id=view_id,
            header=None,
            blocks=[block],
        )

    def _field_map(self, block: FieldsBlock) -> dict[str, ViewFieldDef]:
        out: dict[str, ViewFieldDef] = {}
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
        return replace(
            block,
            fields=only,
            input_mode="prompt",
        )

    async def _validate_all(
        self,
        block: FieldsBlock,
        raw: dict[str, object],
        order: list[str],
    ) -> tuple[dict[str, object], dict[str, list[str]]]:
        out: dict[str, object] = {}
        errors: dict[str, list[str]] = {}

        fields_def = self._field_map(block)

        for key in order:
            fd = fields_def.get(key)
            if fd is None:
                continue

            raw_value = raw.get(key)

            if (
                (raw_value is None or raw_value == "")
                and fd.required
                and not fd.default
            ):
                errors.setdefault(key, []).append("This field is required.")
                continue

            if raw_value is None or raw_value == "":
                raw_value = fd.default

            result = self._policy.validate(
                policy_key=fd.policy,
                raw=raw_value,
            )

            if not result.ok:
                errors.setdefault(key, []).extend(err.message for err in result.errors)
                continue

            out[key] = result.value

        return out, errors

    async def _emit_errors(
        self,
        session: Session,
        errors: dict[str, list[str]],
    ) -> None:
        for key, msgs in errors.items():
            for msg in msgs:
                if key == "form":
                    await session.emit(v_error(msg, error_kind="validation"))
                else:
                    await session.emit(
                        v_error(f"{key}: {msg}", error_kind="validation")
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
