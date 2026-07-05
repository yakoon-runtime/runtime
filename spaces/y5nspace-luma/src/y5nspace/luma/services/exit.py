from __future__ import annotations

from ..data import ExitData
from ..models import Exit
from ..ports import OnDelete, OnGet, OnReplace, OnScan
from .namespaces import exit_key, exit_namespace


class ExitService:

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

    async def _all_exits(self) -> list[Exit]:
        rows = await self._on_scan(namespace=exit_namespace())
        result = []
        for r in rows:
            if r is None:
                continue
            data = ExitData.from_dict(r.require_object())
            result.append(
                Exit(
                    id=r.key.id,
                    world_id=data.world_id,
                    source_box_id=data.source_box_id,
                    target_box_id=data.target_box_id,
                    name=data.name,
                    description=data.description,
                    direction=data.direction,
                )
            )
        return result

    async def get_exit(self, exit_id: str) -> Exit | None:
        row = await self._on_get(key=exit_key(exit_id))
        if row is None or row.data is None:
            return None
        data = ExitData.from_dict(row.require_object())
        return Exit(
            id=exit_id,
            world_id=data.world_id,
            source_box_id=data.source_box_id,
            target_box_id=data.target_box_id,
            name=data.name,
            description=data.description,
            direction=data.direction,
        )

    async def list_exits(self, *, world_id: str) -> list[Exit]:
        return [e for e in await self._all_exits() if e.world_id == world_id]

    async def find_from(self, box_id: str) -> list[Exit]:
        return [e for e in await self._all_exits() if e.source_box_id == box_id]

    async def find_to(self, box_id: str) -> list[Exit]:
        return [e for e in await self._all_exits() if e.target_box_id == box_id]

    async def connect(
        self,
        *,
        world_id: str,
        source_box_id: str,
        target_box_id: str,
        name: str,
        description: str = "",
        direction: str = "",
    ) -> Exit:
        for e in await self._all_exits():
            if e.source_box_id == source_box_id and e.name.lower() == name.lower():
                raise ValueError(f"Exit '{name}' already exists from this box.")
        next_id = await self._on_next_id(prefix="e")
        data = ExitData(
            world_id=world_id,
            source_box_id=source_box_id,
            target_box_id=target_box_id,
            name=name,
            description=description,
            direction=direction,
        )
        await self._on_replace(key=exit_key(str(next_id)), value=data.to_dict())
        return Exit(
            id=str(next_id),
            world_id=world_id,
            source_box_id=source_box_id,
            target_box_id=target_box_id,
            name=name,
            description=description,
            direction=direction,
        )

    async def disconnect(self, exit_id: str) -> None:
        await self._on_delete(key=exit_key(exit_id))
