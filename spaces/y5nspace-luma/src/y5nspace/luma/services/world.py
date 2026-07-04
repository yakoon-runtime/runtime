from __future__ import annotations

from ..models import World
from .contracts import WorldService


class MemoryWorldService(WorldService):

    def __init__(self):
        self._store: dict[str, World] = {}

    async def list_worlds(self) -> list[World]:
        return list(self._store.values())

    async def add_world(self, *, name: str, description: str) -> World:
        if name in self._store:
            raise ValueError(f"World '{name}' already exists.")
        world = World(name=name, description=description)
        self._store[name] = world
        return world

    async def get_world(self, name: str) -> World | None:
        return self._store.get(name)

    async def update_world(self, *, name: str, description: str) -> World:
        if name not in self._store:
            raise ValueError(f"World '{name}' not found.")
        world = self._store[name]
        world.description = description
        return world

    async def delete_world(self, name: str) -> None:
        if name not in self._store:
            raise ValueError(f"World '{name}' not found.")
        del self._store[name]
