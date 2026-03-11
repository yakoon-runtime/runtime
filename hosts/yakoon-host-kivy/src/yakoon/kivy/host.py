from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

from yakoon.base.ui import FieldsBlock
from yakoon.base.ui.document import ViewSpec
from yakoon.platform.hosts import FormInput, HostAdapter, InputEvent, TextInput


class HostUI(Protocol):
    def set_assist(self, text: str, state: str = "question") -> None: ...
    def clear_assist(self) -> None: ...


class NullHostUI:
    def set_assist(self, text: str, state: str = "question") -> None:
        return

    def clear_assist(self) -> None:
        return


class KivyHost(HostAdapter):
    def __init__(
        self,
        *,
        submit: Callable[[InputEvent], Awaitable[None]],
        ui: HostUI | None = None,
    ):
        self._submit = submit
        self._ui: HostUI = ui or NullHostUI()
        self._pending_text: asyncio.Future[str] | None = None
        self._lock = asyncio.Lock()

    def deliver_text(self, *, loop: asyncio.AbstractEventLoop, text: str) -> None:
        fut = self._pending_text
        if not fut or fut.done():
            return
        loop.call_soon_threadsafe(fut.set_result, text)

    async def on_view(self, *, ps1: str, view: ViewSpec) -> None:
        block = self._find_fields_block(view)
        if block is None:
            self._ui.clear_assist()
            return

        if not block.fields:
            self._ui.clear_assist()
            await self._submit(FormInput({}))
            return

        values = await self._read_fields(
            ps1=ps1,
            fields=block.fields[:1] if block.input_mode == "prompt" else block.fields,
        )
        await self._submit(FormInput(values))

    async def _read_field(self, *, ps1: str, fd) -> object:
        key = fd.var or "value"
        title = getattr(fd, "title", None) or key
        self._ui.set_assist(title, state="question")

        loop = asyncio.get_running_loop()
        async with self._lock:
            self._pending_text = loop.create_future()

        text = (await self._pending_text).strip()
        return text

    async def _read_fields(self, *, ps1: str, fields) -> dict[str, object]:
        values: dict[str, object] = {}
        for fd in fields:
            key = fd.var
            if not key:
                continue
            values[key] = await self._read_field(ps1=ps1, fd=fd)
        return values

    async def on_ready(self, *, ps1: str) -> None:
        self._ui.clear_assist()
        loop = asyncio.get_running_loop()
        async with self._lock:
            self._pending_text = loop.create_future()

        text = (await self._pending_text).strip()
        if text:
            await self._submit(TextInput(text))

    async def on_idle(self) -> None:
        return

    async def on_exit(self) -> None:
        return

    def _find_fields_block(self, view: ViewSpec) -> FieldsBlock | None:
        for block in view.blocks:
            if isinstance(block, FieldsBlock) and block.state != "done":
                return block
        return None
