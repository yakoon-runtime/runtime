# console.py

import asyncio
from collections.abc import Awaitable, Callable

from yakoon.base.ui import ViewSpec
from yakoon.base.ui.blocks import FieldsBlock
from yakoon.platform.hosts import (
    FormInput,
    HostAdapter,
    InputEvent,
    TextInput,
    safe_input,
    safe_input_secret,
)


class ConsoleHost(HostAdapter):

    def __init__(
        self,
        submit: Callable[[InputEvent], Awaitable[None]],
    ):
        self._submit = submit
        self._lock = asyncio.Lock()

    async def on_view(self, *, ps1: str, view: ViewSpec):
        for block in view.blocks:
            if isinstance(block, FieldsBlock):
                if block.input_mode == "prompt":
                    values = await self._read_fields(ps1=ps1, fields=block.fields[:1])
                else:
                    values = await self._read_fields(ps1=ps1, fields=block.fields)
                await self._submit(FormInput(values))
                return

    async def on_ready(self, *, ps1: str) -> None:
        async with self._lock:
            text = await safe_input(ps1=ps1)

        if text.strip():
            await self._submit(TextInput(text))

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

    async def _read_fields(self, *, ps1: str, fields) -> dict[str, object]:
        values: dict[str, object] = {}
        for fd in fields:
            key = fd.var
            if key:
                values[key] = await self._read_field(ps1=ps1, fd=fd)
        return values

    async def on_idle(self) -> None:
        return

    async def on_exit(self) -> None:
        return
