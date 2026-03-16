import asyncio
from collections.abc import Awaitable, Callable

from yakoon.base.host import FormInput, InputEvent, Interaction, TextInput
from yakoon.base.ui import FieldsBlock, ViewSpec


class DefaultInteraction(Interaction):

    def __init__(
        self,
        read_input: Callable[[str], Awaitable[str]],
        submit_input: Callable[[InputEvent], Awaitable[None]],
    ):
        self._read_command = read_input
        self._submit_command = submit_input

    async def ready(self, *, ps1: str) -> None:
        try:
            text = await self._read_command(ps1)
        except asyncio.CancelledError:
            return
        if text.strip():
            await self._submit_command(TextInput(text))

    async def prompt(self, *, ps1: str, view: ViewSpec):

        for block in view.blocks:

            if isinstance(block, FieldsBlock):

                if block.input_mode == "prompt":
                    values = await self._read_fields(ps1=ps1, fields=block.fields[:1])
                else:
                    values = await self._read_fields(ps1=ps1, fields=block.fields)

                await self._submit_command(FormInput(values))
                return

    async def idle(self) -> None:
        return

    async def exit(self) -> None:
        pass
        # await self.ui.stop()

    async def _read_field(self, *, ps1: str, fd) -> object:
        key = fd.var or "value"
        label = fd.title or key
        hint = fd.hint or ""

        prompt = label
        if hint:
            prompt = f"{prompt} ({hint})"

        prompt = f"{ps1}[{prompt}]"
        return await self._read_command(prompt)

    async def _read_fields(self, *, ps1: str, fields) -> dict[str, object]:
        values: dict[str, object] = {}
        for fd in fields:
            key = fd.var
            if key:
                values[key] = await self._read_field(ps1=ps1, fd=fd)

        return values
