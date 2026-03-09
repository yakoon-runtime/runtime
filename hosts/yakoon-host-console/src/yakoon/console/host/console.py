import asyncio
from collections.abc import Awaitable, Callable

from yakoon.base.ui import FieldsBlock, ViewSpec
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

    async def on_view(self, *, ps1: str, view: ViewSpec) -> None:
        block = self._find_fields_block(view)
        if block is None:
            return

        if not block.fields:
            await self._submit(FormInput({}))
            return

        values: dict[str, object] = {}

        for fd in block.fields:
            key = fd.var
            if not key:
                continue

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
                    value = await safe_input_secret(ps1=prompt)
                else:
                    value = await safe_input(ps1=prompt)

            values[key] = value

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

    def _find_fields_block(self, view: ViewSpec) -> FieldsBlock | None:
        for block in view.blocks:
            if not isinstance(block, FieldsBlock):
                continue
            if block.state == "done":
                continue
            return block
        return None
