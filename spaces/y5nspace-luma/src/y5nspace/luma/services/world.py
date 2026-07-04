from __future__ import annotations

from ..models import World
from .contracts import WorldService


class MemoryWorldService(WorldService):

    def __init__(self):
        self._store: dict[str, World] = {}
        self._next_id = 1

    def _new_id(self) -> str:
        n = self._next_id
        self._next_id += 1
        return str(n)

    def _find_by_name(self, name: str) -> World | None:
        for w in self._store.values():
            if w.name.lower() == name.lower():
                return w
        return None

    async def list_worlds(self) -> list[World]:
        return list(self._store.values())

    async def add_world(self, *, name: str, description: str) -> World:
        if self._find_by_name(name):
            raise ValueError(f"World '{name}' already exists.")
        world = World(id=self._new_id(), name=name, description=description)
        self._store[world.id] = world
        return world

    async def get_world(self, world_id: str) -> World | None:
        return self._store.get(world_id)

    async def get_world_by_name(self, name: str) -> World | None:
        return self._find_by_name(name)

    async def update_world(self, *, world_id: str, name: str | None, description: str | None, entry_box_id: str | None = None) -> World:
        world = self._store.get(world_id)
        if world is None:
            raise ValueError(f"World '{world_id}' not found.")
        if name is not None:
            other = self._find_by_name(name)
            if other is not None and other.id != world_id:
                raise ValueError(f"World '{name}' already exists.")
            world.name = name
        if description is not None:
            world.description = description
        if entry_box_id is not None:
            world.entry_box_id = entry_box_id
        return world

    async def delete_world(self, world_id: str) -> None:
        if world_id not in self._store:
            raise ValueError(f"World '{world_id}' not found.")
        del self._store[world_id]

    async def set_entry(self, *, world_id: str, box_id: str) -> World:
        world = self._store.get(world_id)
        if world is None:
            raise ValueError(f"World '{world_id}' not found.")
        world.entry_box_id = box_id
        return world
