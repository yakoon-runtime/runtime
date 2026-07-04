from __future__ import annotations

from typing import Protocol

from ..models import World


class WorldService(Protocol):

    async def list_worlds(self) -> list[World]: ...

    async def add_world(self, *, name: str, description: str) -> World: ...

    async def get_world(self, name: str) -> World | None: ...

    async def update_world(self, *, name: str, description: str) -> World: ...

    async def delete_world(self, name: str) -> None: ...
