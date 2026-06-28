from __future__ import annotations

import asyncpg

from ..models import Shard


class PostgresShardRepository:

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def initialize(self):
        self._pool = await asyncpg.create_pool(self._dsn)

    async def shutdown(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._dsn)
        return self._pool

    async def list_shards(self, prefix: str) -> list[Shard]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT prefix, shard_id, range_start, range_end, value, created_at
                FROM id_shards
                WHERE prefix = $1
                ORDER BY shard_id
                """,
                prefix,
            )
        return [Shard.from_row(dict(r)) for r in rows]

    async def delete_shard(self, prefix: str, shard_id: int) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM id_shards WHERE prefix = $1 AND shard_id = $2",
                prefix,
                shard_id,
            )

    async def create_shard(self, shard: Shard) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO id_shards (prefix, shard_id, range_start, range_end, value)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT DO NOTHING
                """,
                shard.prefix,
                shard.shard_id,
                shard.range_start,
                shard.range_end,
                shard.value,
            )

    async def try_increment(
        self, prefix: str, shard_id: int, current_value: int
    ) -> bool:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE id_shards
                SET value = value + 1
                WHERE prefix = $1 AND shard_id = $2 AND value = $3
                """,
                prefix,
                shard_id,
                current_value,
            )
            return result == "UPDATE 1"

    async def get_max_shard_id(self, prefix: str) -> int | None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT MAX(shard_id) AS max_id FROM id_shards WHERE prefix = $1",
                prefix,
            )
            return row["max_id"] if row else None
