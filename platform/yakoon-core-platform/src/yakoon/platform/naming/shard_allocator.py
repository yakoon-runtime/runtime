import random

from .shard import Shard


class DefaultShardAllocator:

    def __init__(self, shard_store, range_size: int = 1000):
        self.shard_store = shard_store
        self.range_size = range_size

    async def pick_writable_shard(self, prefix: str) -> Shard:
        rows = await self.shard_store.list_shards(prefix)
        shards = [Shard.from_row(r) for r in rows]

        # cleanup
        full_shards = [s for s in shards if s.is_full()]
        for shard in full_shards:
            await self.shard_store.delete_shard(shard.prefix, shard.shard_id)

        # verbleibende Kandidaten
        candidates = [s for s in shards if not s.is_full()]
        random.shuffle(candidates)

        for shard in candidates:
            try:
                shard.value += 1
                await self.shard_store.save_shard(shard.to_row())
                return shard
            except Exception:
                continue  # nächster Versuch

        # Alle fehlgeschlagen → neuen Shard erzeugen
        last_id = await self.shard_store.get_max_shard_id(prefix)
        new_start = 0 if last_id is None else last_id + self.range_size
        new_end = new_start + self.range_size

        new_shard = Shard(
            prefix=prefix,
            shard_id=new_start,
            range_start=new_start,
            range_end=new_end,
            value=1,
        )

        await self.shard_store.save_shard(new_shard.to_row())
        return new_shard
