from __future__ import annotations

from ..models import Box
from .contracts import BoxService


class MemoryBoxService(BoxService):

    def __init__(self):
        self._store: dict[str, Box] = {}
        self._next_id = 1

    def _new_id(self) -> str:
        n = self._next_id
        self._next_id += 1
        return str(n)

    async def add_box(
        self, *, world_id: str, parent_id: str | None, name: str, description: str
    ) -> Box:
        for b in self._store.values():
            if b.world_id == world_id and b.name.lower() == name.lower():
                raise ValueError(f"Box '{name}' already exists in this world_id.")
        box = Box(
            id=self._new_id(),
            world_id=world_id,
            parent_id=parent_id,
            name=name,
            description=description,
        )
        self._store[box.id] = box
        return box

    async def get_box(self, box_id: str) -> Box | None:
        return self._store.get(box_id)

    async def list_boxes(self, *, world_id: str, parent_id: str | None) -> list[Box]:
        return [
            b
            for b in self._store.values()
            if b.world_id == world_id and b.parent_id == parent_id
        ]

    async def update_box(self, *, box_id: str, name: str, description: str) -> Box:
        box = self._store.get(box_id)
        if box is None:
            raise ValueError(f"Box '{box_id}' not found.")
        if name != box.name:
            for b in self._store.values():
                if b.world_id == box.world_id and b.name.lower() == name.lower():
                    raise ValueError(f"Box '{name}' already exists in this world_id.")
        box.name = name
        box.description = description
        return box

    async def delete_box(self, box_id: str) -> None:
        if box_id not in self._store:
            raise ValueError(f"Box '{box_id}' not found.")
        del self._store[box_id]
