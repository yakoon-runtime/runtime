from __future__ import annotations

from typing import Protocol

from .models import Shard


class ShardRepository(Protocol):
    async def list_shards(self, prefix: str) -> list[Shard]: ...

    async def delete_shard(self, prefix: str, shard_id: int) -> None: ...

    async def create_shard(self, shard: Shard) -> None: ...

    async def try_increment(
        self, prefix: str, shard_id: int, current_value: int
    ) -> bool: ...

    async def get_max_shard_id(self, prefix: str) -> int | None: ...
