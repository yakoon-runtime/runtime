from __future__ import annotations

import random

from .models import Shard
from .repository import ShardRepository


class ShardAllocator:

    def __init__(self, repository: ShardRepository, range_size: int = 1000):
        self.repository = repository
        self.range_size = range_size

    async def pick_writable_shard(self, prefix: str) -> Shard:
        shards = await self.repository.list_shards(prefix)

        full_shards = [s for s in shards if s.is_full()]
        for shard in full_shards:
            await self.repository.delete_shard(shard.prefix, shard.shard_id)

        candidates = [s for s in shards if not s.is_full()]
        random.shuffle(candidates)

        for shard in candidates:
            ok = await self.repository.try_increment(
                shard.prefix, shard.shard_id, shard.value
            )
            if ok:
                shard.value += 1
                return shard

        last_id = await self.repository.get_max_shard_id(prefix)
        new_start = 0 if last_id is None else last_id + self.range_size
        new_end = new_start + self.range_size

        new_shard = Shard(
            prefix=prefix,
            shard_id=new_start,
            range_start=new_start,
            range_end=new_end,
            value=1,
        )

        await self.repository.create_shard(new_shard)
        return new_shard
