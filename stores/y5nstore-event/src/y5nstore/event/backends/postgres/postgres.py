from __future__ import annotations

import json
from collections.abc import Sequence
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Literal

import asyncpg

from ...models import (
    CurrentRow,
    EntityId,
    IndexQueryTerm,
    IndexSpec,
    IndexTerm,
    IndexValue,
    PatchFormat,
    RevisionRow,
    ValueType,
)
from ...models.mode import ScanMode

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def _norm_value(value_type: ValueType, value: IndexValue) -> str:
    if value_type == ValueType.TEXT:
        return str(value).casefold()
    if value_type == ValueType.INT:
        return f"{int(value):020d}"
    if value_type == ValueType.BOOL:
        return "1" if value else "0"
    return str(value)


# ---------------------------------------------------------
# Backend
# ---------------------------------------------------------


class PostgresBackend:

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None

    # ----------------------------
    # INITIALIZE
    # ----------------------------

    async def initialize(self):
        self.pool = await asyncpg.create_pool(self.dsn)

    # ----------------------------
    # SHOTDOWN
    # ----------------------------

    async def shutdown(self):
        if self.pool:
            await self.pool.close()

    # ----------------------------
    # TRANSACTION
    # ----------------------------

    @asynccontextmanager
    async def transaction(self):
        assert self.pool, "PostgresBackend not initialized"
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield self.bind(conn)

    def exec(self):
        return _PoolExec(self)

    def bind(self, conn):
        return _PostgresExec(conn)

    # -----------------------------------------------------


class _PostgresExec:

    def __init__(self, conn: Any):
        self.conn = conn

    # ----------------------------
    # CURRENT
    # ----------------------------

    async def load_current(self, *, domain_id, kind_id, space_id, entity_id):
        row = await self.conn.fetchrow(
            """
            SELECT rev, data, updated_at
            FROM current
            WHERE domain=$1 AND kind=$2 AND space=$3 AND entity_id=$4
            """,
            str(domain_id),
            str(kind_id),
            str(space_id),
            str(entity_id),
        )

        if not row:
            return None

        data = json.loads(row["data"]) if isinstance(row["data"], str) else row["data"]
        return CurrentRow(
            entity_id=entity_id,
            rev=row["rev"],
            data=data,
            updated_at=row["updated_at"],
        )

    async def load_current_many(
        self,
        *,
        domain_id,
        kind_id,
        space_id,
        entity_ids: Sequence[EntityId],
    ):
        if not entity_ids:
            return {}

        rows = await self.conn.fetch(
            """
            SELECT entity_id, rev, data, updated_at
            FROM current
            WHERE domain=$1 AND kind=$2 AND space=$3
              AND entity_id = ANY($4)
            """,
            str(domain_id),
            str(kind_id),
            str(space_id),
            [str(e) for e in entity_ids],
        )

        return {
            EntityId(r["entity_id"]): CurrentRow(
                entity_id=EntityId(r["entity_id"]),
                rev=r["rev"],
                data=json.loads(r["data"]) if isinstance(r["data"], str) else r["data"],
                updated_at=r["updated_at"],
            )
            for r in rows
        }

    async def upsert_current(
        self,
        *,
        domain_id,
        kind_id,
        space_id,
        entity_id,
        rev,
        data,
        updated_at,
    ):
        await self.conn.execute(
            """
            INSERT INTO current(domain, kind, space, entity_id, rev, data, updated_at)
            VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7)
            ON CONFLICT (domain, kind, space, entity_id)
            DO UPDATE SET
                rev = EXCLUDED.rev,
                data = EXCLUDED.data,
                updated_at = EXCLUDED.updated_at
            """,
            str(domain_id),
            str(kind_id),
            str(space_id),
            str(entity_id),
            rev,
            json.dumps(data),
            updated_at,
        )

    # ----------------------------
    # REVISIONS
    # ----------------------------

    async def append_revision(
        self,
        *,
        domain_id,
        kind_id,
        space_id,
        entity_id,
        rev,
        ts,
        patch_format,
        patch,
    ):
        await self.conn.execute(
            """
            INSERT INTO revisions(domain, kind, space, entity_id, rev, ts, patch, patch_format)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """,
            str(domain_id),
            str(kind_id),
            str(space_id),
            str(entity_id),
            rev,
            ts,
            json.dumps(patch),
            patch_format.value,
        )

    async def load_revisions(
        self,
        *,
        domain_id,
        kind_id,
        space_id,
        entity_id,
        rev_gt,
        ts_lte,
    ):
        rows = await self.conn.fetch(
            """
            SELECT rev, ts, patch, patch_format
            FROM revisions
            WHERE domain=$1 AND kind=$2 AND space=$3 AND entity_id=$4
              AND rev > $5 AND ts <= $6
            ORDER BY rev ASC
            """,
            str(domain_id),
            str(kind_id),
            str(space_id),
            str(entity_id),
            rev_gt,
            ts_lte,
        )

        return [
            RevisionRow(
                entity_id=entity_id,
                rev=r["rev"],
                ts=r["ts"],
                patch=r["patch"],
                patch_format=PatchFormat(r["patch_format"]),
            )
            for r in rows
        ]

    # ----------------------------
    # SNAPSHOT (minimal stub)
    # ----------------------------

    async def load_snapshot_at_or_before(self, **kwargs):
        return None

    async def write_snapshot(self, **kwargs):
        return None

    # ----------------------------
    # INDEX
    # ----------------------------

    async def index_ensure(
        self,
        *,
        domain_id,
        kind_id,
        space_id,
        specs: Sequence[IndexSpec],
    ):
        for spec in specs:
            await self.conn.execute(
                """
                INSERT INTO index_specs(domain, kind, space, key, value_type, unique_flag)
                VALUES ($1,$2,$3,$4,$5,$6)
                ON CONFLICT DO NOTHING
                """,
                str(domain_id),
                str(kind_id),
                str(space_id),
                str(spec.key),
                spec.value_type.value,
                spec.unique,
            )

    async def index_list(self, **kwargs):
        return []

    async def index_replace_terms(
        self,
        *,
        domain_id,
        kind_id,
        space_id,
        entity_id,
        terms: Sequence[IndexTerm],
        written_at: datetime,
    ):
        # delete old
        await self.conn.execute(
            """
            DELETE FROM index_entries
            WHERE domain=$1 AND kind=$2 AND space=$3 AND entity_id=$4
            """,
            str(domain_id),
            str(kind_id),
            str(space_id),
            str(entity_id),
        )

        if not terms:
            return

        # load specs
        rows = await self.conn.fetch(
            """
            SELECT key, value_type
            FROM index_specs
            WHERE domain=$1 AND kind=$2 AND space=$3
            """,
            str(domain_id),
            str(kind_id),
            str(space_id),
        )

        specs = {r["key"]: ValueType(r["value_type"]) for r in rows}

        for t in terms:
            vt = specs.get(str(t.key))
            if vt is None:
                raise KeyError(f"Index not ensured: {t.key}")

            norm = _norm_value(vt, t.value)

            await self.conn.execute(
                """
                INSERT INTO index_entries(
                    domain, kind, space, index_key, value, entity_id, written_at
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7)
                """,
                str(domain_id),
                str(kind_id),
                str(space_id),
                str(t.key),
                norm,
                str(entity_id),
                written_at,
            )

    async def index_scan(
        self,
        *,
        domain_id,
        kind_id,
        space_id,
        index_key,
        mode,
        value,
        lo,
        hi,
        after_value,
        after_entity_id,
        limit,
        as_of,
    ):
        params = [
            str(domain_id),
            str(kind_id),
            str(space_id),
            str(index_key),
        ]

        where = [
            "domain=$1",
            "kind=$2",
            "space=$3",
            "index_key=$4",
            "written_at <= $5",
        ]
        params.append(as_of)

        idx = 6

        if mode == ScanMode.EQ:
            where.append(f"value = ${idx}")
            params.append(value)
            idx += 1
        else:
            if lo is not None:
                where.append(f"value >= ${idx}")
                params.append(lo)
                idx += 1
            if hi is not None:
                where.append(f"value < ${idx}")
                params.append(hi)
                idx += 1

        query = f"""
            SELECT value, entity_id
            FROM index_entries
            WHERE {' AND '.join(where)}
            ORDER BY value, entity_id
            LIMIT ${idx}
        """

        params.append(limit)

        rows = await self.conn.fetch(query, *params)

        return [(r["value"], EntityId(r["entity_id"])) for r in rows]

    async def query_index(
        self,
        *,
        domain_id,
        kind_id,
        space_id,
        terms: Sequence[IndexQueryTerm],
        mode: Literal["and", "or"],
        limit: int = 100,
    ) -> list[EntityId]:

        if not terms:
            return []

        # load specs to normalize values
        rows = await self.conn.fetch(
            """
            SELECT key, value_type
            FROM index_specs
            WHERE domain=$1 AND kind=$2 AND space=$3
            """,
            str(domain_id), str(kind_id), str(space_id),
        )
        specs = {r["key"]: ValueType(r["value_type"]) for r in rows}

        conditions: list[str] = []
        params: list[str] = []
        idx = 4  # first 3 params are domain, kind, space

        for term in terms:
            sk = str(term.index_key)
            vt = specs.get(sk)
            if vt is None:
                continue

            norm = _norm_value(vt, term.value)

            if term.op == "eq":
                conditions.append(f"(index_key = ${idx} AND value = ${idx + 1})")
                params.extend([sk, norm])
                idx += 2

            elif term.op == "prefix":
                conditions.append(f"(index_key = ${idx} AND value ILIKE ${idx + 1} || '%')")
                params.extend([sk, norm])
                idx += 2

            elif term.op == "contains":
                conditions.append(f"(index_key = ${idx} AND value ILIKE '%' || ${idx + 1} || '%')")
                params.extend([sk, norm])
                idx += 2

        if not conditions:
            return []

        where = "domain=$1 AND kind=$2 AND space=$3 AND ({})".format(
            f" {mode.upper()} ".join(conditions),
        )

        if mode == "and":
            having = f"COUNT(DISTINCT index_key) = {len(conditions)}"
            query = f"""
                SELECT entity_id
                FROM index_entries
                WHERE {where}
                GROUP BY entity_id
                HAVING {having}
                LIMIT ${idx}
            """
        else:
            query = f"""
                SELECT DISTINCT entity_id
                FROM index_entries
                WHERE {where}
                LIMIT ${idx}
            """

        params.append(str(limit))

        rows = await self.conn.fetch(query, str(domain_id), str(kind_id), str(space_id), *params)
        return [EntityId(r["entity_id"]) for r in rows]

    # ----------------------------
    # GC (stub)
    # ----------------------------

    async def gc(self, **kwargs):
        return None

    async def gc_global(self, **kwargs):
        return None


class _PoolExec:
    def __init__(self, backend):
        self.backend = backend

    async def _run(self, fn, *args, **kwargs):
        assert self.backend.pool, "PostgresBackend not initialized"
        async with self.backend.pool.acquire() as conn:
            exec = _PostgresExec(conn)
            return await getattr(exec, fn)(*args, **kwargs)

    async def load_current(self, **kwargs):
        return await self._run("load_current", **kwargs)

    async def load_current_many(self, **kwargs):
        return await self._run("load_current_many", **kwargs)

    async def upsert_current(self, **kwargs):
        return await self._run("upsert_current", **kwargs)

    async def append_revision(self, **kwargs):
        return await self._run("append_revision", **kwargs)

    async def load_revisions(self, **kwargs):
        return await self._run("load_revisions", **kwargs)

    async def index_ensure(self, **kwargs):
        return await self._run("index_ensure", **kwargs)

    async def index_list(self, **kwargs):
        return await self._run("index_list", **kwargs)

    async def index_replace_terms(self, **kwargs):
        return await self._run("index_replace_terms", **kwargs)

    async def index_scan(self, **kwargs):
        return await self._run("index_scan", **kwargs)

    async def gc(self, **kwargs):
        return await self._run("gc", **kwargs)

    async def gc_global(self, **kwargs):
        return await self._run("gc_global", **kwargs)

    async def load_snapshot_at_or_before(self, **kwargs):
        return await self._run("load_snapshot_at_or_before", **kwargs)

    async def write_snapshot(self, **kwargs):
        return await self._run("write_snapshot", **kwargs)
