from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

from yakoon.base.ui.view_spec import ViewSpec
from yakoon.platform.hosts.adapter import FormInput, HostAdapter, InputEvent, TextInput


class HostUI(Protocol):
    """Host-lokale UI-API (nicht Engine!), thread-safe zu implementieren."""

    def set_assist(self, text: str, state: str = "question") -> None: ...
    def clear_assist(self) -> None: ...


class NullHostUI:
    def set_assist(self, text: str, state: str = "question") -> None:
        return

    def clear_assist(self) -> None:
        return


class KivyHost(HostAdapter):
    """Minimaler HostAdapter für Kivy.

    - Text-Input: Runner ruft on_ready(); UI liefert Text via deliver_text() (thread-safe).
    - Form-Input: Prompt-basiert feldweise; UI wird via HostUI informiert.
    """

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

        # ! Complete the pending Future from the UI thread.
        # ! This wakes up the asyncio task waiting in on_ready()/on_view().
        loop.call_soon_threadsafe(fut.set_result, text)

    async def on_view(self, *, ps1: str, view: ViewSpec) -> None:
        input_def = view.input
        if not input_def:
            self._ui.clear_assist()
            return

        if input_def.kind != "form":
            raise RuntimeError("KivyHost supports only form inputs")

        fields = input_def.fields or {}
        if not fields:
            self._ui.clear_assist()
            await self._submit(FormInput({}))
            return

        # Engine prompt-mode => exactly one field should be present
        if input_def.input_mode == "prompt":
            field_name = next(iter(fields.keys()))

            print("FIELDNAME ON PROMPT:", repr(field_name))

            fd = fields[field_name]
            title = getattr(fd, "title", None) or field_name
            self._ui.set_assist(title, state="question")

            # ! Create a Future that represents the next user input.
            # ! The coroutine will suspend at 'await' until deliver_text()
            # ! completes this Future from the UI thread.
            loop = asyncio.get_running_loop()
            async with self._lock:
                self._pending_text = loop.create_future()
            text = (await self._pending_text).strip()

            # The coroutine was suspended; the event loop keeps running.
            await self._submit(FormInput({field_name: text}))
            return

        # Batch form-mode (later when FormBlock exists)
        # For now, either raise or fallback to prompt behavior.
        raise RuntimeError(
            "input_mode='form' not supported by Kivy host yet (needs FormBlock UI)"
        )

    async def on_ready(self, *, ps1: str) -> None:
        self._ui.clear_assist()

        # Create an empty Future to wait for the next user input.
        # This does NOT block the thread — the coroutine is suspended
        # while the event loop continues running other tasks.
        loop = asyncio.get_running_loop()
        async with self._lock:
            self._pending_text = loop.create_future()

        # Suspend here until deliver_text() sets the result.
        text = (await self._pending_text).strip()
        if text:
            await self._submit(TextInput(text))

    async def on_idle(self) -> None:
        return

    async def on_exit(self) -> None:
        return
