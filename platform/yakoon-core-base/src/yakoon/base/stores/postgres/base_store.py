import json
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
from pypika import Query, Table

from yakoon.base.models import Key
from yakoon.base.models.ns import Namespace
from yakoon.base.stores.base.base_store import BaseStore


class PostgresStore(BaseStore):
    """
    PostgreSQL-based implementation of BaseStore.
    Uses asyncpg and PyPika for structured access.
    """

    def __init__(self, pool: asyncpg.Pool, table_name: str):
        self.pool = pool
        self.table = Table(table_name)
        self.table_name = table_name

    async def get_by_key(self, key: Key) -> dict | None:
        q = Query.from_(self.table).select("*").where(self.table.__key__ == str(key))
        sql = str(q)
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(sql)
            return dict(row) if row else None

    async def fetch_by_namespace(
        self, namespace: Namespace, *, limit: int = 100
    ) -> list[dict]:
        q = (
            Query.from_(self.table)
            .select("*")
            .where(self.table.__scope__ == namespace.to_str())
            .limit(limit)
        )
        sql = str(q)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql)
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

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql)
            return [dict(row) for row in rows]

    async def save(self, obj: dict) -> None:
        columns = list(obj.keys())
        col_sql = ", ".join(columns)
        placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))

        q = f"""
        INSERT INTO {self.table_name} ({col_sql})
        VALUES ({placeholders})
        ON CONFLICT (__key__) DO UPDATE SET data = EXCLUDED.data;
        """
        values = [
            json.dumps(v) if isinstance(v, (dict, list)) else v for v in obj.values()
        ]

        async with self.pool.acquire() as conn:
            await conn.execute(q, *values)

    async def delete_by_key(self, key: Key) -> None:
        q = Query.from_(self.table).delete().where(self.table.__key__ == str(key))
        sql = str(q)
        async with self.pool.acquire() as conn:
            await conn.execute(sql)

    @asynccontextmanager
    async def _acquire(self):
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)

    @asynccontextmanager
    async def transaction(self):
        conn = await self.pool.acquire()
        tr = conn.transaction()
        await tr.start()
        try:
            yield conn
            await tr.commit()
        except Exception:
            await tr.rollback()
            raise
        finally:
            await self.pool.release(conn)
