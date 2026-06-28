from __future__ import annotations

from ..models import Shard


class MemoryShardRepository:

    def __init__(self):
        self._shards: dict[tuple[str, int], Shard] = {}

    async def list_shards(self, prefix: str) -> list[Shard]:
        return [
            s for (p, _), s in self._shards.items() if p == prefix
        ]

    async def delete_shard(self, prefix: str, shard_id: int) -> None:
        self._shards.pop((prefix, shard_id), None)

    async def create_shard(self, shard: Shard) -> None:
        self._shards[(shard.prefix, shard.shard_id)] = shard

    async def try_increment(
        self, prefix: str, shard_id: int, current_value: int
    ) -> bool:
        shard = self._shards.get((prefix, shard_id))
        if shard is None or shard.value != current_value:
            return False
        return True

    async def get_max_shard_id(self, prefix: str) -> int | None:
        ids = [
            sid for (p, sid) in self._shards if p == prefix
        ]
        return max(ids) if ids else None
