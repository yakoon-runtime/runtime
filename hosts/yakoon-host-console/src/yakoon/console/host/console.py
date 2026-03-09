import asyncio
from collections.abc import Awaitable, Callable

from yakoon.base.ui import FieldsBlock, PatchAppendBlock, PatchAppendChild, ViewEvent
from yakoon.platform.hosts import (
    FormInput,
    HostAdapter,
    InputEvent,
    TextInput,
    safe_input,
    safe_input_secret,
)


class ConsoleHost(HostAdapter):
    """
    Console input adapter (block-driven, silent).

    - does NOT render output (Session/Output owns rendering)
    - collects input from FieldsBlock instances inside view.blocks
    """

    def __init__(self, submit: Callable[[InputEvent], Awaitable[None]]):
        self._submit = submit
        self._lock = asyncio.Lock()

    async def on_view(self, *, ps1: str, event: ViewEvent) -> None:
        block = self._find_fields_block(event)
        if block is None:
            return

        if not block.fields:
            await self._submit(FormInput({}))
            return

        if block.input_mode == "prompt":
            values = await self._read_fields(ps1=ps1, fields=block.fields[:1])
        else:
            values = await self._read_fields(ps1=ps1, fields=block.fields)

        await self._submit(FormInput(values))

    async def on_ready(self, *, ps1: str) -> None:
        async with self._lock:
            text = await safe_input(ps1=ps1)

        if text.strip():
            await self._submit(TextInput(text))

    async def on_idle(self) -> None:
        return

    async def on_exit(self) -> None:
        return

    def _find_fields_block(self, event: ViewEvent) -> FieldsBlock | None:
        for op in event.patch.ops:
            if isinstance(op, PatchAppendBlock):
                block = op.block
            elif isinstance(op, PatchAppendChild):
                block = op.block
            else:
                continue

            if isinstance(block, FieldsBlock) and block.state != "done":
                return block

        return None

    async def _read_field(self, *, ps1: str, fd) -> object:
        key = fd.var or "value"
        label = fd.title or key
        hint = fd.hint or ""
        ui = fd.ui or {}
        secret = bool(ui.get("secret", False))

        prompt = label
        if hint:
            prompt = f"{prompt} ({hint})"
        prompt = f"{ps1}[{prompt}]"

        async with self._lock:
            if secret:
                return await safe_input_secret(ps1=prompt)
            return await safe_input(ps1=prompt)

    async def _read_fields(
        self,
        *,
        ps1: str,
        fields,
    ) -> dict[str, object]:
        values: dict[str, object] = {}

        for fd in fields:
            key = fd.var
            if not key:
                continue

            values[key] = await self._read_field(ps1=ps1, fd=fd)

        return values
