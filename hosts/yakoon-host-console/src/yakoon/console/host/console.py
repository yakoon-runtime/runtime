# yakoon/console/host.py
import asyncio
from collections.abc import Awaitable, Callable

from yakoon.base.models.view import ViewSpec
from yakoon.platform.hosts.adapter import FormInput, HostAdapter, InputEvent, TextInput
from yakoon.platform.hosts.input import safe_input, safe_input_secret


class ConsoleHost(HostAdapter):
    """
    Console input adapter (view-driven, silent).

    - does NOT render output (Session/Output owns rendering)
    - only collects input from view.input and submits values
    """

    def __init__(self, submit: Callable[[InputEvent], Awaitable[None]]):
        self._submit = submit
        self._lock = asyncio.Lock()

    async def on_view(self, *, ps1: str, view: ViewSpec) -> None:
        input_def = view.input
        if not input_def:
            return
        if input_def.kind != "form":
            raise RuntimeError("ConsoleHost supports only form inputs")

        fields = input_def.fields or {}
        if not isinstance(fields, dict) or not fields:
            await self._submit(FormInput({}))
            return

        values: dict[str, object] = {}

        for key, fd in fields.items():
            label = fd.title or key
            hint = getattr(fd, "hint", "") or ""
            ui = fd.ui or {}
            secret = bool(ui.get("secret", False))

            prompt = label
            if hint:
                prompt = f"{prompt} ({hint})"
            prompt = f"{ps1}[{prompt}]"

            async with self._lock:
                secret = bool(ui.get("secret", False))
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
