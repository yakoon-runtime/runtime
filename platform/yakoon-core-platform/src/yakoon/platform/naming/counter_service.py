from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .shard_allocator import DefaultShardAllocator


class DefaultCounterService:

    def __init__(self, allocator: DefaultShardAllocator):
        self.allocator = allocator

    async def next(self, prefix: str) -> str:
        shard = await self.allocator.pick_writable_shard(prefix)
        return str(shard.range_start + shard.value)
