from __future__ import annotations

from ..data import BoxData
from ..models import Box
from ..ports import OnDelete, OnGet, OnReplace, OnScan
from .namespaces import box_key, box_namespace


class BoxService:

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

    async def _all_boxes(self) -> list[Box]:
        rows = await self._on_scan(namespace=box_namespace())
        result = []
        for r in rows:
            if r is None:
                continue
            data = BoxData.from_dict(r.require_object())
            result.append(
                Box(
                    id=r.key.id,
                    world_id=data.world_id,
                    parent_id=data.parent_id,
                    name=data.name,
                    description=data.description,
                    portable=data.portable,
                )
            )
        return result

    async def add_box(
        self,
        *,
        world_id: str,
        parent_id: str | None,
        name: str,
        description: str,
        portable: bool = False,
    ) -> Box:
        for b in await self._all_boxes():
            if b.world_id == world_id and b.name.lower() == name.lower():
                raise ValueError(f"Box '{name}' already exists in this world.")
        next_id = await self._on_next_id(prefix="b")
        data = BoxData(
            world_id=world_id,
            parent_id=parent_id,
            name=name,
            description=description,
            portable=portable,
        )
        await self._on_replace(key=box_key(str(next_id)), value=data.to_dict())
        return Box(
            id=str(next_id),
            world_id=world_id,
            parent_id=parent_id,
            name=name,
            description=description,
            portable=portable,
        )

    async def get_box(self, box_id: str) -> Box | None:
        row = await self._on_get(key=box_key(box_id))
        if row is None or row.data is None:
            return None
        data = BoxData.from_dict(row.require_object())
        return Box(
            id=box_id,
            world_id=data.world_id,
            parent_id=data.parent_id,
            name=data.name,
            description=data.description,
            portable=data.portable,
        )

    async def list_boxes(self, *, world_id: str, parent_id: str | None) -> list[Box]:
        return [
            b
            for b in await self._all_boxes()
            if b.world_id == world_id and b.parent_id == parent_id
        ]

    async def update_box(self, *, box_id: str, name: str, description: str) -> Box:
        box = await self.get_box(box_id)
        if box is None:
            raise ValueError(f"Box '{box_id}' not found.")
        if name.lower() != box.name.lower():
            for b in await self._all_boxes():
                if b.world_id == box.world_id and b.name.lower() == name.lower():
                    raise ValueError(f"Box '{name}' already exists in this world.")
        data = BoxData(
            world_id=box.world_id,
            parent_id=box.parent_id,
            name=name,
            description=description,
            portable=box.portable,
        )
        await self._on_replace(key=box_key(box_id), value=data.to_dict())
        return Box(
            id=box_id,
            world_id=box.world_id,
            parent_id=box.parent_id,
            name=name,
            description=description,
            portable=box.portable,
        )

    async def delete_box(self, box_id: str) -> None:
        await self._on_delete(key=box_key(box_id))

    async def move_box(self, box_id: str, new_parent_id: str | None) -> Box:
        box = await self.get_box(box_id)
        if box is None:
            raise ValueError(f"Box '{box_id}' not found.")
        if not box.portable:
            raise ValueError(f"Box '{box.name}' is not portable.")
        data = BoxData(
            world_id=box.world_id,
            parent_id=new_parent_id,
            name=box.name,
            description=box.description,
            portable=box.portable,
        )
        await self._on_replace(key=box_key(box_id), value=data.to_dict())
        return Box(
            id=box_id,
            world_id=box.world_id,
            parent_id=new_parent_id,
            name=box.name,
            description=box.description,
            portable=box.portable,
        )

    async def find_box(self, *, world_id: str, name: str) -> Box | None:
        for b in await self._all_boxes():
            if b.world_id == world_id and b.name.lower() == name.lower():
                return b
        return None
