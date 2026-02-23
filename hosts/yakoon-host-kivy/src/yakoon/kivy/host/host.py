from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from yakoon.base.models.view import ViewSpec
from yakoon.platform.hosts.adapter import FormInput, HostAdapter, InputEvent, TextInput


class KivyHost(HostAdapter):
    """Minimaler HostAdapter für Kivy.

    - Text-Input: Runner ruft on_ready(); UI liefert Text via deliver_text() (thread-safe).
    - Form-Input: aktuell minimal als auto-submit {} (bis Form-UI verdrahtet ist).
    """

    def __init__(self, *, submit: Callable[[InputEvent], Awaitable[None]]):
        self._submit = submit
        self._pending_text: asyncio.Future[str] | None = None
        self._lock = asyncio.Lock()

    def deliver_text(self, *, loop: asyncio.AbstractEventLoop, text: str) -> None:
        fut = self._pending_text
        if not fut or fut.done():
            return
        loop.call_soon_threadsafe(fut.set_result, text)

    async def on_view(self, *, ps1: str, view: ViewSpec) -> None:
        input_def = view.input
        if not input_def:
            return

        if input_def.kind != "form":
            raise RuntimeError("KivyHost supports only form inputs")

        fields = input_def.fields or {}
        if not fields:
            await self._submit(FormInput({}))
            return

        # Minimal: wir nehmen an, es gibt genau 1 Feld
        field_name = next(iter(fields.keys()))

        loop = asyncio.get_running_loop()
        async with self._lock:
            self._pending_text = loop.create_future()

        text = (await self._pending_text).strip()
        await self._submit(FormInput({field_name: text}))

    async def on_ready(self, *, ps1: str) -> None:
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
