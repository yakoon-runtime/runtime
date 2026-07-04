from __future__ import annotations

from ..models import Exit
from .contracts import ExitService


class MemoryExitService(ExitService):

    def __init__(self):
        self._store: dict[str, Exit] = {}
        self._next_id = 1

    def _new_id(self) -> str:
        n = self._next_id
        self._next_id += 1
        return str(n)

    async def get_exit(self, exit_id: str) -> Exit | None:
        return self._store.get(exit_id)

    async def list_exits(self, *, world_id: str) -> list[Exit]:
        return [e for e in self._store.values() if e.world_id == world_id]

    async def find_from(self, box_id: str) -> list[Exit]:
        return [e for e in self._store.values() if e.source_box_id == box_id]

    async def find_to(self, box_id: str) -> list[Exit]:
        return [e for e in self._store.values() if e.target_box_id == box_id]

    async def connect(self, *, world_id: str, source_box_id: str, target_box_id: str, name: str, description: str = "", direction: str = "") -> Exit:
        for e in self._store.values():
            if e.source_box_id == source_box_id and e.name.lower() == name.lower():
                raise ValueError(f"Exit '{name}' already exists from this box.")
        exit = Exit(
            id=self._new_id(),
            world_id=world_id,
            source_box_id=source_box_id,
            target_box_id=target_box_id,
            name=name,
            description=description,
            direction=direction,
        )
        self._store[exit.id] = exit
        return exit

    async def disconnect(self, exit_id: str) -> None:
        if exit_id not in self._store:
            raise ValueError(f"Exit '{exit_id}' not found.")
        del self._store[exit_id]
