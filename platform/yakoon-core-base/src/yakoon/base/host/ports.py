from __future__ import annotations

from typing import Protocol

from yakoon.base.ui import ViewSpec


class Interaction(Protocol):
    """
    InteractionAdapter is the UI boundary.

    Engine -> UI only.
    UI -> Engine goes via Runner callbacks.
    """

    async def prompt(self, *, ps1: str, view: ViewSpec) -> None: ...
    async def ready(self, *, ps1: str) -> None: ...
    async def idle(self) -> None: ...
    async def exit(self) -> None: ...
