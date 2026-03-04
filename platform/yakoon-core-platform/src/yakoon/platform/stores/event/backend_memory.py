from __future__ import annotations

import asyncio
import bisect
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from yakoon.base.stores.event.entity import (
    DomainId,
    EntityId,
    IndexKey,
    IndexSpec,
    IndexTerm,
    IndexValue,
    JsonValue,
    KindId,
    PatchFormat,
    RetentionPolicy,
    SpaceId,
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


def _ns_key(domain_id: DomainId, kind_id: KindId, space_id: SpaceId) -> str:
    return f"{domain_id}::{kind_id}::{space_id}"


def _ent_key(
    domain_id: DomainId, kind_id: KindId, space_id: SpaceId, entity_id: EntityId
) -> tuple[str, str, str, str]:
    return (str(domain_id), str(kind_id), str(space_id), str(entity_id))


class MemoryBackend(EntityStoreBackend):
    """
    Dev/test backend.
    - single-process only
    - transactional semantics provided by an asyncio lock (coarse-grained but correct)
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

        # current: (domain,kind,space,entity) -> CurrentRow
        self._current: dict[tuple[str, str, str, str], CurrentRow] = {}

        # revisions: (domain,kind,space,entity) -> list[RevisionRow] sorted by rev
        self._revisions: dict[tuple[str, str, str, str], list[RevisionRow]] = {}

        # snapshots: (domain,kind,space,entity) -> list[SnapshotRow] sorted by ts
        self._snapshots: dict[tuple[str, str, str, str], list[SnapshotRow]] = {}

        # index specs: (domain,kind,space) -> dict[IndexKey, IndexSpec]
        self._index_specs: dict[tuple[str, str, str], dict[str, IndexSpec]] = {}

        # index data:
        # - forward: (domain,kind,space,entity) -> dict[index_key -> IndexValue]
        self._index_terms_by_entity: dict[
            tuple[str, str, str, str], dict[str, IndexValue]
        ] = {}
        # - inverted: (domain,kind,space,index_key,value_norm) -> sorted list of _IndexRecord
        self._index_inv: dict[tuple[str, str, str, str, str], list[_IndexRecord]] = {}

    def transaction(self) -> EntityStoreBackendTx:
        return _MemoryTx(self)


class _MemoryTx(EntityStoreBackendTx):
    def __init__(self, backend: MemoryBackend) -> None:
        self._b = backend

    async def __aenter__(self) -> EntityStoreBackendTx:
        await self._b._lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool | None:
        self._b._lock.release()
        return None

    # --- helpers ---

    def _k(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
    ) -> tuple[str, str, str, str]:
        return _ent_key(domain_id, kind_id, space_id, entity_id)

    def _sp(
        self, *, domain_id: DomainId, kind_id: KindId, space_id: SpaceId
    ) -> tuple[str, str, str]:
        return (str(domain_id), str(kind_id), str(space_id))

    def _norm_value(self, spec: IndexSpec, value: IndexValue) -> str:
        if spec.value_type is ValueType.TEXT:
            if not isinstance(value, str):
                raise TypeError("IndexValue must be str for TEXT index")
            return value.casefold()
        if spec.value_type is ValueType.INT:
            if not isinstance(value, int):
                raise TypeError("IndexValue must be int for INT index")
            return f"{value:020d}"
        if spec.value_type is ValueType.BOOL:
            if not isinstance(value, bool):
                raise TypeError("IndexValue must be bool for BOOL index")
            return "1" if value else "0"
        # fallback
        return str(value)

    # --- entity materialization ---

    async def load_current(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
    ) -> CurrentRow | None:
        return self._b._current.get(
            self._k(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
                entity_id=entity_id,
            )
        )

    async def load_current_many(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_ids: Sequence[EntityId],
    ) -> Mapping[EntityId, CurrentRow]:

        result: dict[EntityId, CurrentRow] = {}

        for eid in entity_ids:
            key = (domain_id, kind_id, space_id, eid)
            row = self._b._current.get(key)
            if row is not None:
                result[eid] = row

        return result

    async def upsert_current(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        rev: int,
        data: JsonValue,
        updated_at: datetime,
    ) -> None:
        self._b._current[
            self._k(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
                entity_id=entity_id,
            )
        ] = CurrentRow(
            entity_id=entity_id,
            rev=rev,
            data=data,
            updated_at=updated_at,
        )

    async def append_revision(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        rev: int,
        ts: datetime,
        patch_format: PatchFormat,
        patch: JsonValue,
    ) -> None:
        k = self._k(
            domain_id=domain_id, kind_id=kind_id, space_id=space_id, entity_id=entity_id
        )
        rows = self._b._revisions.setdefault(k, [])
        rows.append(
            RevisionRow(
                entity_id=entity_id,
                rev=rev,
                ts=ts,
                patch=patch,
                patch_format=patch_format,
            )
        )
        rows.sort(key=lambda r: r.rev)

    async def load_revisions(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        rev_gt: int,
        ts_lte: datetime,
    ) -> Sequence[RevisionRow]:
        k = self._k(
            domain_id=domain_id, kind_id=kind_id, space_id=space_id, entity_id=entity_id
        )
        rows = self._b._revisions.get(k, [])
        return [r for r in rows if r.rev > rev_gt and r.ts <= ts_lte]

    async def load_snapshot_at_or_before(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        ts_lte: datetime,
    ) -> SnapshotRow | None:
        k = self._k(
            domain_id=domain_id, kind_id=kind_id, space_id=space_id, entity_id=entity_id
        )
        snaps = self._b._snapshots.get(k, [])
        # snaps sorted by ts
        i = bisect.bisect_right([s.ts for s in snaps], ts_lte) - 1
        if i < 0:
            return None
        return snaps[i]

    async def write_snapshot(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        rev: int,
        ts: datetime,
        data: JsonValue,
    ) -> None:
        k = self._k(
            domain_id=domain_id, kind_id=kind_id, space_id=space_id, entity_id=entity_id
        )
        snaps = self._b._snapshots.setdefault(k, [])
        snaps.append(SnapshotRow(entity_id=entity_id, rev=rev, ts=ts, data=data))
        snaps.sort(key=lambda s: s.ts)

    # --- index structures & data ---

    async def index_ensure(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        specs: Sequence[IndexSpec],
    ) -> None:
        sp = self._sp(domain_id=domain_id, kind_id=kind_id, space_id=space_id)
        table = self._b._index_specs.setdefault(sp, {})
        for spec in specs:
            key = str(spec.key)
            if key in table:
                # idempotent: do not silently change spec
                if table[key] != spec:
                    raise ValueError(f"IndexSpec change requires migration: {key}")
            else:
                table[key] = spec

    async def index_list(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
    ) -> Sequence[IndexSpec]:
        sp = self._sp(domain_id=domain_id, kind_id=kind_id, space_id=space_id)
        return list(self._b._index_specs.get(sp, {}).values())

    async def index_scan(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        index_key: IndexKey,
        mode: str,  # "eq" | "range"
        value: IndexValue | None = None,
        lo: IndexValue | None = None,
        hi: IndexValue | None = None,
        after_value: IndexValue | None = None,
        after_entity_id: EntityId | None = None,
        limit: int = 100,
    ) -> list[tuple[IndexValue, EntityId]]:

        rows: list[tuple[IndexValue, EntityId]] = []

        # normalize once
        after_value_norm: str | None = (
            _norm_index_value(after_value) if after_value is not None else None
        )
        after_entity_id_norm: EntityId | None = after_entity_id

        value_norm_query: str | None = None
        lo_norm: str | None = None
        hi_norm: str | None = None

        if mode == "eq":
            assert value is not None
            value_norm_query = _norm_index_value(value)
        else:
            lo_norm = _norm_index_value(lo) if lo is not None else None
            hi_norm = _norm_index_value(hi) if hi is not None else None

        for (
            domain,
            kind,
            space,
            index_key_i,
            value_norm,
        ), records in self._b._index_inv.items():

            if domain != domain_id or kind != kind_id or space != space_id:
                continue
            if index_key_i != index_key:
                continue

            # bucket-level filter
            if mode == "eq":
                # only this one value bucket is relevant
                if value_norm_query is not None and value_norm != value_norm_query:
                    continue
            else:
                if lo_norm is not None and value_norm < lo_norm:
                    continue
                if hi_norm is not None and value_norm > hi_norm:
                    continue

                # keyset across buckets: skip buckets strictly before cursor
                if after_value_norm is not None and value_norm < after_value_norm:
                    continue

            # record-level filter (needs eid)
            for rec in records:
                eid = rec.entity_id

                if after_value_norm is not None:
                    if value_norm < after_value_norm:
                        continue
                    if (
                        value_norm == after_value_norm
                        and after_entity_id_norm is not None
                        and eid <= after_entity_id_norm
                    ):
                        continue

                # for EQ, cursor uses same boundary rule, already handled above
                rows.append((value_norm, eid))

        rows.sort(key=lambda x: (x[0], x[1]))
        return rows[:limit]

    async def index_replace_terms(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        terms: Sequence[IndexTerm],
    ) -> None:
        sp = self._sp(domain_id=domain_id, kind_id=kind_id, space_id=space_id)
        specs = self._b._index_specs.get(sp, {})
        if not specs:
            return

        ent_k = self._k(
            domain_id=domain_id, kind_id=kind_id, space_id=space_id, entity_id=entity_id
        )

        # remove old postings for keys we are about to set
        existing = self._b._index_terms_by_entity.get(ent_k, {})
        for t in terms:
            k = str(t.key)
            old = existing.get(k)
            if old is None:
                continue
            spec = specs.get(k)
            if spec is None:
                continue
            old_norm = self._norm_value(spec, old)
            inv_k = (str(domain_id), str(kind_id), str(space_id), k, old_norm)
            lst = self._b._index_inv.get(inv_k, [])
            lst = [r for r in lst if r.entity_id != entity_id]
            if lst:
                self._b._index_inv[inv_k] = lst
            else:
                self._b._index_inv.pop(inv_k, None)

        # apply new
        newmap = dict(existing)
        for t in terms:
            k = str(t.key)
            spec = specs.get(k)
            if spec is None:
                raise KeyError(f"Index not ensured: {k}")
            norm = self._norm_value(spec, t.value)

            newmap[k] = t.value
            inv_k = (str(domain_id), str(kind_id), str(space_id), k, norm)
            lst = self._b._index_inv.setdefault(inv_k, [])
            rec_key = f"{norm}::{entity_id}"
            rec = _IndexRecord(key=rec_key, entity_id=entity_id)
            # insert sorted
            i = bisect.bisect_left([r.key for r in lst], rec.key)
            if i >= len(lst) or lst[i].entity_id != entity_id:
                lst.insert(i, rec)

        self._b._index_terms_by_entity[ent_k] = newmap

    # --- maintenance ---

    async def gc(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        policy: RetentionPolicy,
        now: datetime,
    ) -> None:
        cutoff = now - timedelta(days=policy.keep_revisions_days)

        # prune revisions and snapshots
        for k in list(self._b._revisions.keys()):
            d, kd, s, _ = k
            if d == str(domain_id) and kd == str(kind_id) and s == str(space_id):
                self._b._revisions[k] = [
                    r for r in self._b._revisions[k] if r.ts >= cutoff
                ]
                if not self._b._revisions[k]:
                    self._b._revisions.pop(k, None)

        snap_cutoff = now - timedelta(days=policy.keep_snapshots_days or 0)
        for k in list(self._b._snapshots.keys()):
            d, kd, s, _ = k
            if d == str(domain_id) and kd == str(kind_id) and s == str(space_id):
                self._b._snapshots[k] = [
                    r for r in self._b._snapshots[k] if r.ts >= snap_cutoff
                ]
                if not self._b._snapshots[k]:
                    self._b._snapshots.pop(k, None)


def _norm_index_value(value: IndexValue) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        # fixed width for correct lexical ordering if you want numeric range
        # choose width big enough for your domain, or use signed prefix.
        return f"i:{value:020d}"
    if isinstance(value, float):
        return f"f:{value:030.10f}"
    if isinstance(value, str):
        return f"s:{value}"
    if value is None:
        return "n:"
    raise TypeError(f"Unsupported IndexValue: {type(value)}")
