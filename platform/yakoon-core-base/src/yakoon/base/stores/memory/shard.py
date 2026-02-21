class InMemoryShardCounterStore:

    def __init__(self):
        self._shards: list[dict] = []

    async def list_shards(self, prefix: str) -> list[dict]:
        return [row for row in self._shards if row["prefix"] == prefix]

    async def delete_shard(self, prefix: str, shard_id: int) -> None:
        self._data.pop((prefix, shard_id), None)

    async def save_shard(self, row: dict):
        for idx, existing in enumerate(self._shards):
            if (
                existing["shard_id"] == row["shard_id"]
                and existing["prefix"] == row["prefix"]
            ):
                self._shards[idx] = row
                return
        self._shards.append(row)

    async def get_max_shard_id(self, prefix: str) -> int:
        return max(
            (row["shard_id"] for row in self._shards if row["prefix"] == prefix),
            default=0,
        )
