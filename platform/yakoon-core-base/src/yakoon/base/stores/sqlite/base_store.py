from contextlib import asynccontextmanager
from typing import Any

import aiosqlite
from pypika import Query, Table

from yakoon.base.models.key import Key
from yakoon.base.models.ns import Namespace
from yakoon.base.stores.base.base_store import BaseStore


class SQLiteStore(BaseStore):
    """
    SQLite-based implementation of BaseStore.
    Uses aiosqlite and PyPika for efficient and structured SQL interaction.
    """

    def __init__(self, db_path: str, table_name: str):
        self.db_path = db_path
        self.table = Table(table_name)
        self.table_name = table_name

    async def get_by_key(self, key: Key) -> dict | None:
        q = Query.from_(self.table).select("*").where(self.table.__key__ == str(key))
        sql = str(q)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def fetch_by_namespace(
        self, namespace: Namespace, *, limit: int = 100
    ) -> list[dict]:
        scope = namespace.to_str()
        q = (
            Query.from_(self.table)
            .select("*")
            .where(self.table.__scope__ == scope)
            .limit(limit)
        )
        sql = str(q)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def fetch_by_fields(
        self, *, namespace: Namespace, limit: int = 100, **fields: Any
    ) -> list[dict]:
        q = (
            Query.from_(self.table)
            .select("*")
            .where(self.table.__scope__ == namespace.to_str())
        )

        for key, value in fields.items():
            q = q.where(self.table[key] == value)

        q = q.limit(limit)
        sql = str(q)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def save(self, obj: dict) -> None:
        columns = list(obj.keys())
        placeholders = ", ".join(["?"] * len(columns))
        col_sql = ", ".join(columns)

        update_fields = [
            col for col in columns if col != "__key__" and col != "__created_at__"
        ]
        update_clause = ", ".join(f"{col} = excluded.{col}" for col in update_fields)

        q = f"""
        INSERT INTO {self.table_name} ({col_sql})
        VALUES ({placeholders})
        ON CONFLICT(__key__) DO UPDATE SET {update_clause};
        """

        values = list(obj.values())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(q, values)
            await db.commit()

    async def delete_by_key(self, key: Key) -> None:
        q = Query.from_(self.table).delete().where(self.table.__key__ == str(key))
        sql = str(q)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(sql)
            await db.commit()

    @asynccontextmanager
    async def _connect(self):
        db = await aiosqlite.connect(self.db_path)
        db.row_factory = aiosqlite.Row
        try:
            yield db
        finally:
            await db.close()

    @asynccontextmanager
    async def transaction(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("BEGIN")
            try:
                yield db
                await db.commit()
            except Exception:
                await db.rollback()
                raise
