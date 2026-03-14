import asyncio
from collections.abc import Awaitable, Callable

from yakoon.base.ui import FieldsBlock, ViewSpec
from yakoon.platform.hosts import (
    FormInput,
    HostAdapter,
    InputEvent,
    TextInput,
)


class ConsoleHost(HostAdapter):

    def __init__(
        self,
        ui,
        submit: Callable[[InputEvent], Awaitable[None]],
    ):
        self.ui = ui
        self._submit = submit

    async def on_ready(self, *, ps1: str) -> None:
        try:
            text = await self.ui.read_line(ps1)
        except asyncio.CancelledError:
            return
        if text.strip():
            await self._submit(TextInput(text))

    async def on_prompt(self, *, ps1: str, view: ViewSpec):

        for block in view.blocks:

            if isinstance(block, FieldsBlock):

                if block.input_mode == "prompt":
                    values = await self._read_fields(ps1=ps1, fields=block.fields[:1])
                else:
                    values = await self._read_fields(ps1=ps1, fields=block.fields)

                await self._submit(FormInput(values))
                return

    async def on_idle(self) -> None:
        return

    async def on_exit(self) -> None:
        await self.ui.stop()

    async def _read_field(self, *, ps1: str, fd) -> object:

        key = fd.var or "value"
        label = fd.title or key
        hint = fd.hint or ""

        prompt = label
        if hint:
            prompt = f"{prompt} ({hint})"

        prompt = f"{ps1}[{prompt}]"

        return await self.ui.read_line(prompt)

    async def _read_fields(self, *, ps1: str, fields) -> dict[str, object]:

        values: dict[str, object] = {}

        for fd in fields:
            key = fd.var
            if key:
                values[key] = await self._read_field(ps1=ps1, fd=fd)

        return values
