from __future__ import annotations

import asyncio
import bisect
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..models.entity import (
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
from ..models.mode import ScanMode
from ..models.rows import CurrentRow, RevisionRow, SnapshotRow


@dataclass(slots=True)
class _IndexRecord:
    # stable sort key for pagination
    key: str
    entity_id: EntityId
    written_at: datetime


def _ent_key(
    domain_id: DomainId, kind_id: KindId, space_id: SpaceId, entity_id: EntityId
) -> tuple[str, str, str, str]:
    return (str(domain_id), str(kind_id), str(space_id), str(entity_id))


class MemoryBackend:
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
        # (domain,kind,space,index_key) -> (value_norm -> sorted list[_IndexRecord])
        self._index_inv2: dict[
            tuple[str, str, str, str],
            dict[str, list[_IndexRecord]],
        ] = {}

    def transaction(self) -> MemoryTransactionScope:
        return MemoryTransactionScope(self)

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
        key = self._k(
            domain_id=domain_id,
            kind_id=kind_id,
            space_id=space_id,
            entity_id=entity_id,
        )
        return self._current.get(key)

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
            key = self._k(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
                entity_id=eid,
            )

            row = self._current.get(key)
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
        self._current[
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
        rows = self._revisions.setdefault(k, [])
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
        rows = self._revisions.get(k, [])

        return sorted(
            (r for r in rows if r.rev > rev_gt and r.ts <= ts_lte),
            key=lambda r: r.rev,
        )

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
        snaps = self._snapshots.get(k, [])
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
        snaps = self._snapshots.setdefault(k, [])
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
        table = self._index_specs.setdefault(sp, {})
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
        return list(self._index_specs.get(sp, {}).values())

    async def index_scan(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        index_key: IndexKey,
        mode: ScanMode,  # "eq" | "range"
        value: IndexValue | None = None,
        lo: IndexValue | None = None,
        hi: IndexValue | None = None,
        after_value: IndexValue | None = None,
        after_entity_id: EntityId | None = None,
        limit: int = 100,
        as_of: datetime | None = None,
    ) -> list[tuple[IndexValue, EntityId]]:

        rows: list[tuple[IndexValue, EntityId]] = []

        if mode not in (ScanMode.EQ, ScanMode.RANGE):
            raise ValueError(f"unsupported scan mode: {mode}")

        gkey = (str(domain_id), str(kind_id), str(space_id), str(index_key))
        sp = self._sp(domain_id=domain_id, kind_id=kind_id, space_id=space_id)
        specs = self._index_specs.get(sp, {})
        spec = specs.get(str(index_key))
        if spec is None:
            return []

        bucket = self._index_inv2.get(gkey)
        if not bucket:
            return []

        # normalize cursor
        after_value_norm = (
            self._norm_value(spec, after_value) if after_value is not None else None
        )
        after_entity_id_norm = after_entity_id

        # ------------------------
        # EQ mode
        # ------------------------
        if mode == ScanMode.EQ:
            assert value is not None

            vq = self._norm_value(spec, value)

            # cursor may already be past this bucket
            if after_value_norm is not None and after_value_norm > vq:
                return []

            records = bucket.get(vq, [])

            for rec in records:
                if as_of is not None and rec.written_at > as_of:
                    continue

                eid = rec.entity_id

                if after_value_norm is not None:
                    if (
                        vq == after_value_norm
                        and after_entity_id_norm is not None
                        and eid <= after_entity_id_norm
                    ):
                        continue

                rows.append((value, eid))

                if len(rows) >= limit:
                    break

            return rows

        # ------------------------
        # RANGE mode
        # ------------------------
        lo_norm = self._norm_value(spec, lo) if lo is not None else None
        hi_norm = self._norm_value(spec, hi) if hi is not None else None

        values = sorted(bucket.keys())

        start = 0
        if lo_norm is not None:
            start = bisect.bisect_left(values, lo_norm)

        # cursor may push start further
        if after_value_norm is not None:
            start = max(start, bisect.bisect_left(values, after_value_norm))

        for value_norm in values[start:]:

            if hi_norm is not None and value_norm > hi_norm:
                break

            # skip values strictly before cursor
            if after_value_norm is not None and value_norm < after_value_norm:
                continue

            for rec in bucket[value_norm]:

                # continue if out of page frame
                if as_of is not None and rec.written_at > as_of:
                    continue

                eid = rec.entity_id

                if after_value_norm is not None:
                    if (
                        value_norm == after_value_norm
                        and after_entity_id_norm is not None
                        and eid <= after_entity_id_norm
                    ):
                        continue

                rows.append((value_norm, eid))

                if len(rows) >= limit:
                    return rows

        return rows

    async def index_replace_terms(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        terms: Sequence[IndexTerm],
        written_at: datetime,
    ) -> None:
        sp = self._sp(domain_id=domain_id, kind_id=kind_id, space_id=space_id)
        specs = self._index_specs.get(sp, {})
        if not specs:
            return

        ent_k = self._k(
            domain_id=domain_id, kind_id=kind_id, space_id=space_id, entity_id=entity_id
        )

        # remove old postings for keys we are about to set
        existing = self._index_terms_by_entity.get(ent_k, {})
        for t in terms:
            k = str(t.key)
            old = existing.get(k)
            if old is None:
                continue
            spec = specs.get(k)
            if spec is None:
                continue

            old_norm = self._norm_value(spec, old)

            gkey = (str(domain_id), str(kind_id), str(space_id), k)
            bucket = self._index_inv2.get(gkey)
            if not bucket:
                continue

            lst = bucket.get(old_norm, [])
            lst = [r for r in lst if r.entity_id != entity_id]
            if lst:
                bucket[old_norm] = lst
            else:
                bucket.pop(old_norm, None)

            if not bucket:
                self._index_inv2.pop(gkey, None)

        # apply new
        newmap = dict(existing)
        for t in terms:
            k = str(t.key)
            spec = specs.get(k)
            if spec is None:
                raise KeyError(f"Index not ensured: {k}")

            norm = self._norm_value(spec, t.value)
            newmap[k] = t.value

            gkey = (str(domain_id), str(kind_id), str(space_id), k)
            bucket = self._index_inv2.setdefault(gkey, {})
            lst = bucket.setdefault(norm, [])

            # UNIQUE check (optional but strongly recommended)
            if spec.unique and lst and all(r.entity_id != entity_id for r in lst):
                raise ValueError(f"Unique index violation for {k}={t.value}")

            rec_key = f"{norm}::{entity_id}"
            rec = _IndexRecord(key=rec_key, entity_id=entity_id, written_at=written_at)

            # insert sorted
            i = bisect.bisect_left([r.key for r in lst], rec.key)
            if i >= len(lst) or lst[i].entity_id != entity_id:
                lst.insert(i, rec)

        self._index_terms_by_entity[ent_k] = newmap

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
        for k in list(self._revisions.keys()):
            d, kd, s, _ = k
            if d == str(domain_id) and kd == str(kind_id) and s == str(space_id):
                self._revisions[k] = [r for r in self._revisions[k] if r.ts >= cutoff]
                if not self._revisions[k]:
                    self._revisions.pop(k, None)

        snap_cutoff = now - timedelta(days=policy.keep_snapshots_days or 0)
        for k in list(self._snapshots.keys()):
            d, kd, s, _ = k
            if d == str(domain_id) and kd == str(kind_id) and s == str(space_id):
                self._snapshots[k] = [
                    r for r in self._snapshots[k] if r.ts >= snap_cutoff
                ]
                if not self._snapshots[k]:
                    self._snapshots.pop(k, None)

    async def gc_global(self, *, policy: RetentionPolicy) -> None:
        return None


# ----------------------------------
# TRANSACTION SCOPE
# ----------------------------------


class MemoryTransactionScope:

    def __init__(self, backend):
        self._b = backend

    async def __aenter__(self):
        await self._b._lock.acquire()
        return self._b

    async def __aexit__(self, *args):
        self._b._lock.release()
