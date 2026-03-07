from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from yakoon.base.ui.view_spec import ViewSpec


@dataclass(frozen=True)
class TextInput:
    value: str


@dataclass(frozen=True)
class FormInput:
    data: dict[str, object]


InputEvent = TextInput | FormInput


class HostAdapter(Protocol):
    """
    HostAdapter is the UI boundary.

    Engine -> UI only.
    UI -> Engine goes via Runner callbacks.
    """

    async def on_view(self, *, ps1: str, view: ViewSpec) -> None: ...
    async def on_ready(self, *, ps1: str) -> None: ...
    async def on_idle(self) -> None: ...
    async def on_exit(self) -> None: ...
