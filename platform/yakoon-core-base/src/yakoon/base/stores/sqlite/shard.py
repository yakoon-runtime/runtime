import aiosqlite


class SQLiteShardCounterStore:

    def __init__(self, db_path: str, table_name: str = "shards"):
        self.db_path = db_path
        self.table_name = table_name

    async def _connect(self):
        return await aiosqlite.connect(self.db_path)

    async def list_shards(self, prefix: str) -> list[dict]:
        query = f"SELECT * FROM {self.table_name} WHERE prefix = ?"
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, (prefix,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def delete_shard(self, prefix: str, shard_id: int) -> None:
        query = f"""
        DELETE FROM {self.table_name}
        WHERE prefix = ? AND shard_id = ?
        """
        async with self._connect() as db:
            await db.execute(query, (prefix, shard_id))
            await db.commit()

    async def save_shard(self, row: dict):
        query = f"""
        INSERT INTO {self.table_name} (prefix, shard_id, range_start, range_end, value, created_at)
        VALUES (:prefix, :shard_id, :range_start, :range_end, :value, :created_at)
        ON CONFLICT(prefix, shard_id)
        DO UPDATE SET
            range_start = excluded.range_start,
            range_end = excluded.range_end,
            value = excluded.value,
            created_at = excluded.created_at
        """  # noqa: E501
        async with self._connect() as db:
            await db.execute(query, row)
            await db.commit()

    async def get_max_shard_id(self, prefix: str) -> int:
        query = f"SELECT MAX(shard_id) FROM {self.table_name} WHERE prefix = ?"
        async with self._connect() as db:
            cursor = await db.execute(query, (prefix,))
            row = await cursor.fetchone()
            return row[0] if row[0] is not None else 0
