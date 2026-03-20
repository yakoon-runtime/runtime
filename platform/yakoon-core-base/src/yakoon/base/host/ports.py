from __future__ import annotations

from typing import Protocol

from yakoon.base.ui import ViewSpec


class Interaction(Protocol):

    async def show_prompt(self, ps1: str) -> None: ...
    async def show_view(self, view: ViewSpec) -> None: ...
    async def exit(self) -> None: ...
