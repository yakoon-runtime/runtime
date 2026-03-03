from __future__ import annotations

import asyncio
import bisect
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from yakoon.base.stores.event.entity import (
    EntityId,
    IndexKey,
    IndexSpec,
    IndexTerm,
    IndexValue,
    JsonValue,
    PluginGroup,
    RetentionPolicy,
    ScopeId,
    ValueType,
)
from yakoon.platform.stores.event.backend import (
    CurrentRow,
    EntityStoreBackend,
    EntityStoreBackendTx,
    RevisionRow,
    SnapshotRow,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class _IndexRecord:
    # stable sort key for pagination
    key: str
    entity_id: EntityId


def _scope_pg_key(scope_id: ScopeId, plugin_group: PluginGroup) -> str:
    return f"{scope_id}::{plugin_group}"


class MemoryBackend(EntityStoreBackend):
    """
    Dev/test backend.
    - single-process only
    - transactional semantics provided by an asyncio lock (coarse-grained but correct)
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

        # current: (scope,plugin,entity) -> CurrentRow
        self._current: dict[tuple[str, str, str], CurrentRow] = {}

        # revisions: (scope,plugin,entity) -> list[RevisionRow] sorted by rev
        self._revisions: dict[tuple[str, str, str], list[RevisionRow]] = {}

        # snapshots: (scope,plugin,entity) -> list[SnapshotRow] sorted by ts
        self._snapshots: dict[tuple[str, str, str], list[SnapshotRow]] = {}

        # index specs: (scope,plugin) -> dict[IndexKey, IndexSpec]
        self._index_specs: dict[tuple[str, str], dict[str, IndexSpec]] = {}

        # index data:
        # - forward: (scope,plugin,entity) -> dict[index_key -> IndexValue]
        self._index_terms_by_entity: dict[
            tuple[str, str, str], dict[str, IndexValue]
        ] = {}
        # - inverted: (scope,plugin,index_key,value_norm) -> sorted list of _IndexRecord
        self._index_inv: dict[tuple[str, str, str, str], list[_IndexRecord]] = {}

    def transaction(self) -> EntityStoreBackendTx:
        return _MemoryTx(self)


class _MemoryTx(EntityStoreBackendTx):
    def __init__(self, backend: MemoryBackend) -> None:
        self._b = backend

    async def __aenter__(self) -> _MemoryTx:
        await self._b._lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool | None:
        self._b._lock.release()
        return False

    # ---- helpers ----

    def _k(
        self, scope_id: ScopeId, plugin_group: PluginGroup, entity_id: EntityId
    ) -> tuple[str, str, str]:
        return (str(scope_id), str(plugin_group), str(entity_id))

    def _sp(self, scope_id: ScopeId, plugin_group: PluginGroup) -> tuple[str, str]:
        return (str(scope_id), str(plugin_group))

    def _normalize_index_value(self, spec: IndexSpec, value: IndexValue) -> str:
        # Keep it predictable for lookups/pagination.
        # For TIME/UUID you likely store as TEXT in dev anyway.
        vt = spec.value_type
        if vt == ValueType.INT:
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"Index {spec.key} expects int")
            return f"i:{value}"
        if vt == ValueType.BOOL:
            if not isinstance(value, bool):
                raise TypeError(f"Index {spec.key} expects bool")
            return f"b:{'1' if value else '0'}"
        if vt == ValueType.FLOAT:
            if not isinstance(value, float):
                # allow int? your call; I keep strict.
                raise TypeError(f"Index {spec.key} expects float")
            return f"f:{value!r}"
        # TEXT / TIME / UUID -> store as str
        if not isinstance(value, str):
            raise TypeError(f"Index {spec.key} expects str")
        return f"s:{value}"

    # ---- current ----

    async def load_current(
        self, *, scope_id: ScopeId, plugin_group: PluginGroup, entity_id: EntityId
    ) -> CurrentRow | None:
        return self._b._current.get(self._k(scope_id, plugin_group, entity_id))

    async def upsert_current(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        entity_id: EntityId,
        rev: int,
        data: JsonValue,
        updated_at: datetime,
    ) -> None:
        self._b._current[self._k(scope_id, plugin_group, entity_id)] = CurrentRow(
            entity_id=entity_id,
            rev=rev,
            data=data,
            updated_at=updated_at,
        )

    # ---- revisions ----

    async def append_revision(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        entity_id: EntityId,
        rev: int,
        ts: datetime,
        patch: JsonValue,
    ) -> None:
        k = self._k(scope_id, plugin_group, entity_id)
        lst = self._b._revisions.setdefault(k, [])
        # enforce monotonic rev
        if lst and rev <= lst[-1].rev:
            raise RuntimeError(f"Non-monotonic rev for {k}: {rev} <= {lst[-1].rev}")
        lst.append(RevisionRow(entity_id=entity_id, rev=rev, ts=ts, patch=patch))

    async def load_revisions(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        entity_id: EntityId,
        rev_gt: int,
        ts_lte: datetime,
    ) -> Sequence[RevisionRow]:
        k = self._k(scope_id, plugin_group, entity_id)
        lst = self._b._revisions.get(k, [])
        # lst sorted by rev; filter by rev and ts
        return [r for r in lst if r.rev > rev_gt and r.ts <= ts_lte]

    # ---- snapshots ----

    async def load_snapshot_at_or_before(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        entity_id: EntityId,
        ts_lte: datetime,
    ) -> SnapshotRow | None:
        k = self._k(scope_id, plugin_group, entity_id)
        lst = self._b._snapshots.get(k, [])
        if not lst:
            return None
        # lst sorted by ts
        # find rightmost <= ts_lte
        ts_list = [s.ts for s in lst]
        idx = bisect.bisect_right(ts_list, ts_lte) - 1
        if idx < 0:
            return None
        return lst[idx]

    async def write_snapshot(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        entity_id: EntityId,
        rev: int,
        ts: datetime,
        data: JsonValue,
    ) -> None:
        k = self._k(scope_id, plugin_group, entity_id)
        lst = self._b._snapshots.setdefault(k, [])
        # keep sorted by ts (append if monotonic; else insert)
        if not lst or ts >= lst[-1].ts:
            lst.append(SnapshotRow(entity_id=entity_id, rev=rev, ts=ts, data=data))
            return
        ts_list = [s.ts for s in lst]
        idx = bisect.bisect_right(ts_list, ts)
        lst.insert(idx, SnapshotRow(entity_id=entity_id, rev=rev, ts=ts, data=data))

    # ---- index registry ----

    async def index_ensure(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        specs: Sequence[IndexSpec],
    ) -> None:
        sp = self._sp(scope_id, plugin_group)
        reg = self._b._index_specs.setdefault(sp, {})
        for spec in specs:
            key = str(spec.key)
            if key in reg:
                # idempotent; do not silently change existing definition
                old = reg[key]
                if old.value_type != spec.value_type or old.unique != spec.unique:
                    raise RuntimeError(f"IndexSpec change requires migration: {key}")
                continue
            reg[key] = spec

    async def index_list(
        self, *, scope_id: ScopeId, plugin_group: PluginGroup
    ) -> Sequence[IndexSpec]:
        sp = self._sp(scope_id, plugin_group)
        reg = self._b._index_specs.get(sp, {})
        return list(reg.values())

    # ---- index data (index-on-write) ----

    async def index_replace_terms(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        entity_id: EntityId,
        terms: Sequence[IndexTerm],
    ) -> None:
        if not terms:
            return

        sp = self._sp(scope_id, plugin_group)
        reg = self._b._index_specs.get(sp, {})

        entk = self._k(scope_id, plugin_group, entity_id)
        prev = self._b._index_terms_by_entity.setdefault(entk, {})

        # Remove old postings for the keys we are about to write
        for term in terms:
            k = str(term.key)
            if k in prev:
                old_val = prev[k]
                spec = reg.get(k)
                if spec is None:
                    # if index isn't registered, treat as config error
                    raise RuntimeError(f"Index key not registered: {k}")
                old_norm = self._normalize_index_value(spec, old_val)
                invk = (str(scope_id), str(plugin_group), k, old_norm)
                bucket = self._b._index_inv.get(invk, [])
                rec_key = f"{k}|{old_norm}|{entity_id}"
                # bucket is sorted by record.key
                keys = [r.key for r in bucket]
                i = bisect.bisect_left(keys, rec_key)
                if i < len(bucket) and bucket[i].key == rec_key:
                    bucket.pop(i)

        # Insert new postings
        for term in terms:
            k = str(term.key)
            spec = reg.get(k)
            if spec is None:
                raise RuntimeError(f"Index key not registered: {k}")

            norm = self._normalize_index_value(spec, term.value)
            prev[k] = term.value

            invk = (str(scope_id), str(plugin_group), k, norm)
            bucket = self._b._index_inv.setdefault(invk, [])

            rec_key = f"{k}|{norm}|{entity_id}"
            record = _IndexRecord(key=rec_key, entity_id=entity_id)

            keys = [r.key for r in bucket]
            i = bisect.bisect_left(keys, rec_key)
            if i < len(bucket) and bucket[i].key == rec_key:
                continue  # idempotent write
            bucket.insert(i, record)

            if spec.unique:
                # enforce uniqueness for this (key, norm) pair
                # if unique, bucket must have at most 1 entity
                # (we allow the same entity overwriting itself)
                if len(bucket) > 1:
                    raise RuntimeError(f"Unique index violation for {k}={term.value}")

    async def index_query_ids(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        index_key: IndexKey,
        value: IndexValue,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[EntityId], str | None]:
        sp = self._sp(scope_id, plugin_group)
        reg = self._b._index_specs.get(sp, {})
        k = str(index_key)
        spec = reg.get(k)
        if spec is None:
            raise RuntimeError(f"Index key not registered: {k}")

        norm = self._normalize_index_value(spec, value)
        invk = (str(scope_id), str(plugin_group), k, norm)
        bucket = self._b._index_inv.get(invk, [])

        start = 0
        if cursor:
            keys = [r.key for r in bucket]
            start = bisect.bisect_right(keys, cursor)

        page = bucket[start : start + max(0, limit)]
        ids = [r.entity_id for r in page]

        next_cursor = None
        if len(page) == limit and page:
            next_cursor = page[-1].key

        return ids, next_cursor

    # ---- GC ----

    async def gc(
        self,
        *,
        scope_id: ScopeId | None,
        plugin_group: PluginGroup | None,
        policy: RetentionPolicy,
        now: datetime,
    ) -> None:
        # For dev/test: simple delete by timestamp.
        # In Postgres you will likely do partition-drop.
        cutoff_rev = now - timedelta(days=policy.keep_revisions_days)
        cutoff_snap = None
        if policy.keep_snapshots_days is not None:
            cutoff_snap = now - timedelta(days=policy.keep_snapshots_days)

        def _match(spk: tuple[str, str, str]) -> bool:
            s, p, _ = spk
            if scope_id is not None and s != str(scope_id):
                return False
            if plugin_group is not None and p != str(plugin_group):
                return False
            return True

        # revisions
        for k in list(self._b._revisions.keys()):
            if not _match(k):
                continue
            self._b._revisions[k] = [
                r for r in self._b._revisions[k] if r.ts >= cutoff_rev
            ]
            if not self._b._revisions[k]:
                self._b._revisions.pop(k, None)

        # snapshots
        if cutoff_snap is not None:
            for k in list(self._b._snapshots.keys()):
                if not _match(k):
                    continue
                self._b._snapshots[k] = [
                    s for s in self._b._snapshots[k] if s.ts >= cutoff_snap
                ]
                if not self._b._snapshots[k]:
                    self._b._snapshots.pop(k, None)

        # index cleanup: optional; for dev we can skip, but we can also remove postings
        # for entities that no longer exist in current (rare in your flow).
        # We'll keep it simple and leave index as-is for now.
