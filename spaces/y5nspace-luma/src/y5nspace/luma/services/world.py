from __future__ import annotations

from ..data import WorldData
from ..models import World
from ..ports import OnDelete, OnGet, OnReplace, OnScan
from .namespaces import world_key, world_namespace


class WorldService:

    def __init__(
        self,
        on_get: OnGet,
        on_replace: OnReplace,
        on_scan: OnScan,
        on_delete: OnDelete,
        on_next_id,
    ):
        self._on_get = on_get
        self._on_replace = on_replace
        self._on_scan = on_scan
        self._on_delete = on_delete
        self._on_next_id = on_next_id

    async def list_worlds(self) -> list[World]:
        rows = await self._on_scan(namespace=world_namespace())
        return [self._to_world(r) for r in rows if r is not None]

    async def add_world(self, *, name: str, description: str) -> World:
        existing = await self.get_world_by_name(name)
        if existing:
            raise ValueError(f"World '{name}' already exists.")
        next_id = await self._on_next_id(prefix="w")
        key = world_key(str(next_id))
        data = WorldData(name=name, description=description)
        await self._on_replace(key=key, value=data.to_dict())
        return World(id=str(next_id), name=name, description=description)

    async def get_world(self, world_id: str) -> World | None:
        row = await self._on_get(key=world_key(world_id))
        if row is None or row.data is None:
            return None
        data = WorldData.from_dict(row.require_object())
        return World(
            id=world_id,
            name=data.name,
            description=data.description,
            entry_box_id=data.entry_box_id,
        )

    async def get_world_by_name(self, name: str) -> World | None:
        worlds = await self.list_worlds()
        for w in worlds:
            if w.name.lower() == name.lower():
                return w
        return None

    async def update_world(
        self,
        *,
        world_id: str,
        name: str | None,
        description: str | None,
        entry_box_id: str | None = None,
    ) -> World:
        world = await self.get_world(world_id)
        if world is None:
            raise ValueError(f"World '{world_id}' not found.")
        new_name = name if name is not None else world.name
        if new_name.lower() != world.name.lower():
            existing = await self.get_world_by_name(new_name)
            if existing and existing.id != world_id:
                raise ValueError(f"World '{new_name}' already exists.")
        new_desc = description if description is not None else world.description
        new_entry = entry_box_id if entry_box_id is not None else world.entry_box_id
        data = WorldData(name=new_name, description=new_desc, entry_box_id=new_entry)
        await self._on_replace(key=world_key(world_id), value=data.to_dict())
        return World(
            id=world_id, name=new_name, description=new_desc, entry_box_id=new_entry
        )

    async def delete_world(self, world_id: str) -> None:
        await self._on_delete(key=world_key(world_id))

    async def set_entry(self, *, world_id: str, box_id: str) -> World:
        return await self.update_world(
            world_id=world_id, name=None, description=None, entry_box_id=box_id
        )

    def _to_world(self, row) -> World:
        data = WorldData.from_dict(row.require_object())
        return World(
            id=row.key.id,
            name=data.name,
            description=data.description,
            entry_box_id=data.entry_box_id,
        )
