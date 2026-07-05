from __future__ import annotations

import base64
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Literal, Protocol

from y5n.base.naming import Key, Namespace

from .models import (
    CurrentRow,
    DomainId,
    EntityId,
    GetResult,
    IndexKey,
    IndexQueryTerm,
    IndexSpec,
    IndexTerm,
    IndexValue,
    JsonValue,
    KindId,
    PatchFormat,
    PatchStrategy,
    PutResult,
    RetentionPolicy,
    RevisionRow,
    ScanCursor,
    ScanMode,
    SnapshotHint,
    SnapshotPolicy,
    SnapshotRow,
    SpaceId,
)


class EntityStore:

    def __init__(
        self,
        *,
        on_load_current: OnLoadCurrent,
        on_load_current_many: OnLoadCurrentMany,
        on_load_revisions: OnLoadRevisions,
        on_load_snapshot: OnLoadSnapshot,
        on_append_revision: OnAppendRevision,
        on_upsert_current: OnUpsertCurrent,
        on_write_snapshot: OnWriteSnapshot,
        on_index_ensure: OnIndexEnsure,
        on_index_list: OnIndexList,
        on_index_replace_terms: OnIndexReplaceTerms,
        on_index_scan: OnIndexScan,
        on_query_index: OnQueryIndex,
        on_gc: OnGC,
        on_gc_global: OnGCGlobal,
        writer: PatchStrategy,
        readers: Mapping[PatchFormat, PatchStrategy],
    ):
        self.on_load_current = on_load_current
        self.on_load_current_many = on_load_current_many
        self.on_load_revisions = on_load_revisions
        self.on_load_snapshot = on_load_snapshot

        self.on_append_revision = on_append_revision
        self.on_upsert_current = on_upsert_current
        self.on_write_snapshot = on_write_snapshot

        self.on_index_ensure = on_index_ensure
        self.on_index_list = on_index_list
        self.on_index_replace_terms = on_index_replace_terms
        self.on_index_scan = on_index_scan
        self.on_query_index = on_query_index

        self.on_gc = on_gc
        self.on_gc_global = on_gc_global

        self._writer = writer
        self._readers = dict(readers)
        self._readers.setdefault(writer.format, writer)

        self._snap = SnapshotPolicy()
        self._enable_revisions = True

    # ----------------------------
    # Index
    # ----------------------------

    async def ensure_indexes(self, *, namespace: Namespace, specs: Sequence[IndexSpec]):
        d, k, s = _dims_from_namespace(namespace)
        await self.on_index_ensure(domain_id=d, kind_id=k, space_id=s, specs=specs)

    async def list_indexes(self, *, namespace: Namespace):
        d, k, s = _dims_from_namespace(namespace)
        return await self.on_index_list(domain_id=d, kind_id=k, space_id=s)

    # ----------------------------
    # APPEND
    # ----------------------------

    async def append(
        self,
        *,
        key: Key,
        patch: JsonValue,
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, object] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult:
        _ = meta  # meta reserved for future use

        self._writer.validate(patch)
        now = _utc_now()

        d, k, s, eid = _dims_from_key(key)

        cur = await self.on_load_current(
            domain_id=d, kind_id=k, space_id=s, entity_id=eid
        )

        if cur is None:
            cur_rev = 0
            cur_state = None
            last_snapshot_rev = 0
            last_snapshot_ts = None
        else:
            cur_rev = cur.rev
            cur_state = cur.data

            snap = await self.on_load_snapshot(
                domain_id=d, kind_id=k, space_id=s, entity_id=eid, ts_lte=now
            )

            last_snapshot_rev = 0 if snap is None else snap.rev
            last_snapshot_ts = None if snap is None else snap.ts

        if expected_rev is not None and expected_rev != cur_rev:
            raise ConcurrencyError()

        strat = self._readers[self._writer.format]
        new_state = strat.apply(current=cur_state, patch=patch)
        new_rev = cur_rev + 1

        if self._enable_revisions:
            await self.on_append_revision(
                domain_id=d,
                kind_id=k,
                space_id=s,
                entity_id=eid,
                rev=new_rev,
                ts=now,
                patch_format=self._writer.format,
                patch=patch,
            )

        await self.on_upsert_current(
            domain_id=d,
            kind_id=k,
            space_id=s,
            entity_id=eid,
            rev=new_rev,
            data=new_state,
            updated_at=now,
        )

        if indexes:
            await self.on_index_replace_terms(
                domain_id=d,
                kind_id=k,
                space_id=s,
                entity_id=eid,
                terms=indexes,
                written_at=now,
            )

        snapshot_written = False
        if await self._should_snapshot(
            snapshot_hint=snapshot_hint,
            new_rev=new_rev,
            last_snapshot_rev=last_snapshot_rev,
            now=now,
            last_snapshot_ts=last_snapshot_ts,
        ):
            await self.on_write_snapshot(
                domain_id=d,
                kind_id=k,
                space_id=s,
                entity_id=eid,
                rev=new_rev,
                ts=now,
                data=new_state,
            )
            snapshot_written = True

        return PutResult(
            entity_id=eid,
            rev=new_rev,
            updated_at=now,
            snapshot_written=snapshot_written,
        )

    # ----------------------------
    # REPLACE FULL DOC
    # ----------------------------

    async def replace(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        expected_rev: int | None = None,
    ) -> PutResult:

        row = await self.get(key=key)

        patch = self._writer.create_full_replace(
            current=row.data if row else None,
            new_doc=doc,
        )

        return await self.append(
            key=key,
            patch=patch,
            indexes=indexes,
            snapshot_hint=snapshot_hint,
            expected_rev=expected_rev,
        )

    # ----------------------------
    # DELETE (Tombstone)
    # ----------------------------

    async def delete(
        self,
        *,
        key: Key,
        meta: Mapping[str, object] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult:
        patch = self._writer.create_tombstone()
        result = await self.append(
            key=key,
            patch=patch,
            indexes=(),  # don't update via append
            meta=meta,
            expected_rev=expected_rev,
        )
        d, k, s, eid = _dims_from_key(key)
        await self.on_index_replace_terms(
            domain_id=d,
            kind_id=k,
            space_id=s,
            entity_id=eid,
            terms=[],
            written_at=result.updated_at,
        )
        return result

    # ----------------------------
    # GET (inkl. Historie)
    # ----------------------------

    async def get(
        self,
        *,
        key: Key,
        at_time: datetime | None = None,
    ) -> GetResult:

        d, k, s, eid = _dims_from_key(key)

        # ----------------------------------
        # CURRENT (fast path)
        # ----------------------------------
        if at_time is None:
            cur = await self.on_load_current(
                domain_id=d,
                kind_id=k,
                space_id=s,
                entity_id=eid,
            )

            if cur is None:
                return GetResult(
                    key=key,
                    entity_id=eid,
                    data=None,
                    rev=None,
                    as_of=_utc_now(),
                    historical=False,
                )

            return GetResult(
                key=key,
                entity_id=eid,
                data=cur.data,
                rev=cur.rev,
                as_of=cur.updated_at,
                historical=False,
            )

        # ----------------------------------
        # HISTORICAL (snapshot + replay)
        # ----------------------------------
        t = at_time

        snap = await self.on_load_snapshot(
            domain_id=d,
            kind_id=k,
            space_id=s,
            entity_id=eid,
            ts_lte=t,
        )

        if snap is None:
            base_state = None
            base_rev = 0
            last_rev = None  # WICHTIG (nicht 0!)
        else:
            base_state = snap.data
            base_rev = snap.rev
            last_rev = snap.rev

        revs = await self.on_load_revisions(
            domain_id=d,
            kind_id=k,
            space_id=s,
            entity_id=eid,
            rev_gt=base_rev,
            ts_lte=t,
        )

        state = base_state

        for r in revs:
            strat = self._readers.get(r.patch_format)
            if strat is None:
                raise RuntimeError(
                    f"No patch reader registered for format={r.patch_format}"
                )

            state = strat.apply(current=state, patch=r.patch)
            last_rev = r.rev

        return GetResult(
            key=key,
            entity_id=eid,
            data=state,
            rev=last_rev,
            as_of=t,
            historical=True,
        )

    # ----------------------------
    # GET MANY
    # ----------------------------

    async def get_many(self, *, keys: Sequence[Key]) -> list[GetResult]:

        if not keys:
            return []

        groups = defaultdict(list)
        for idx, key in enumerate(keys):
            d, k, s, eid = _dims_from_key(key)
            groups[(d, k, s)].append((idx, key, eid))

        results: list[GetResult | None] = [None] * len(keys)
        now = _utc_now()

        for (d, k, s), items in groups.items():

            eids = [eid for _, _, eid in items]
            unique_eids = list(dict.fromkeys(eids))

            rows = await self.on_load_current_many(
                domain_id=d,
                kind_id=k,
                space_id=s,
                entity_ids=unique_eids,
            )

            for idx, key, eid in items:
                row = rows.get(eid)

                results[idx] = GetResult(
                    key=key,
                    entity_id=eid,
                    data=None if row is None else row.data,
                    rev=None if row is None else row.rev,
                    as_of=now if row is None else row.updated_at,
                    historical=False,
                )

        return [r for r in results if r is not None]

    # ----------------------------
    # SCAN (final)
    # ----------------------------

    async def scan(
        self,
        *,
        namespace: Namespace,
        index_key: IndexKey,
        value: IndexValue | None = None,
        lo: IndexValue | None = None,
        hi: IndexValue | None = None,
        limit: int = 100,
        prefix: str | None = None,
        cursor: str | None = None,
    ) -> tuple[list[Key], str | None]:

        d, k, s = _dims_from_namespace(namespace)
        mode = ScanMode.EQ if value is not None else ScanMode.RANGE

        after_value = None
        after_entity_id = None

        if cursor:
            c = decode_cursor(cursor)

            if c.index_key != str(index_key) or c.mode != mode:
                raise ValueError("cursor mismatch")

            after_value = c.value
            after_entity_id = EntityId(c.entity_id)

            as_of = datetime.fromisoformat(c.asof)
            if as_of.tzinfo is None:
                raise ValueError("cursor asof must be timezone-aware")

            # optional: normalize
            as_of = as_of.astimezone(UTC)

        else:
            as_of = _utc_now()

        if prefix is not None:
            if value is not None:
                raise ValueError("prefix + value not allowed")
            if lo is not None or hi is not None:
                raise ValueError("prefix + range not allowed")

            lo = prefix
            hi = prefix_end(prefix)

        rows = await self.on_index_scan(
            domain_id=d,
            kind_id=k,
            space_id=s,
            index_key=index_key,
            mode=mode,
            value=value,
            lo=lo,
            hi=hi,
            after_value=after_value,
            after_entity_id=after_entity_id,
            limit=limit,
            as_of=as_of,
        )

        keys = [
            Key.from_parts(
                domain=namespace.domain,
                kind=namespace.kind,
                space=namespace.space,
                id=str(eid),
            )
            for _, eid in rows
        ]

        next_cursor = None
        if rows:
            v, eid = rows[-1]
            next_cursor = encode_cursor(
                ScanCursor(
                    index_key=str(index_key),
                    mode=mode,
                    value=v,
                    entity_id=str(eid),
                    asof=as_of.astimezone(UTC).isoformat(),  # keep stable across pages
                )
            )

        return keys, next_cursor

    async def query_index(
        self,
        *,
        namespace: Namespace,
        terms: Sequence[IndexQueryTerm],
        mode: Literal["and", "or"],
        limit: int = 100,
    ) -> tuple[list[Key], str | None]:
        d, k, s = _dims_from_namespace(namespace)
        entity_ids = await self.on_query_index(
            domain_id=d,
            kind_id=k,
            space_id=s,
            terms=terms,
            mode=mode,
            limit=limit,
        )
        keys = [
            Key.from_parts(
                domain=namespace.domain,
                kind=namespace.kind,
                space=namespace.space,
                id=str(eid),
            )
            for eid in entity_ids
        ]
        return keys, None

    # ----------------------------
    # GC
    # ----------------------------

    async def gc(self, *, namespace: Namespace, policy: RetentionPolicy):
        d, k, s = _dims_from_namespace(namespace)
        await self.on_gc(
            domain_id=d, kind_id=k, space_id=s, policy=policy, now=_utc_now()
        )

    async def gc_global(self, *, policy: RetentionPolicy):
        await self.on_gc_global(policy=policy)

    async def _should_snapshot(
        self,
        *,
        snapshot_hint: SnapshotHint,
        new_rev: int,
        last_snapshot_rev: int,
        now: datetime,
        last_snapshot_ts: datetime | None,
    ) -> bool:
        if snapshot_hint is SnapshotHint.COMMIT:
            return True

        if new_rev - last_snapshot_rev >= self._snap.every_n_revisions:
            return True

        if last_snapshot_ts is None:
            return True

        age = (now - last_snapshot_ts).total_seconds()
        return age >= self._snap.max_age_seconds


# ============================================================
# Helpers
# ============================================================


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _dims_from_namespace(ns: Namespace):
    return DomainId(ns.domain), KindId(ns.kind), SpaceId(ns.space)


def _dims_from_key(key: Key):
    d, k, s = _dims_from_namespace(key.namespace)
    return d, k, s, EntityId(key.id)


def prefix_end(prefix: str) -> str | None:
    if prefix == "":
        return None
    chars = list(prefix)
    for i in range(len(chars) - 1, -1, -1):
        cp = ord(chars[i])
        if cp < 0x10FFFF:
            chars[i] = chr(cp + 1)
            return "".join(chars[: i + 1])
    return None


# ============================================================
# Cursor
# ============================================================


def encode_cursor(c: ScanCursor) -> str:
    raw = json.dumps(
        {
            "ik": c.index_key,
            "m": c.mode.value,
            "v": c.value,
            "id": c.entity_id,
            "asof": c.asof,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> ScanCursor:
    pad = "=" * (-len(cursor) % 4)
    raw = base64.urlsafe_b64decode((cursor + pad).encode("ascii"))
    obj = json.loads(raw.decode("utf-8"))
    asof = obj.get("asof")
    if asof is None:
        raise ValueError("cursor missing required field: asof")

    return ScanCursor(
        index_key=str(obj["ik"]),
        mode=ScanMode(obj["m"]),
        value=obj.get("v"),
        entity_id=str(obj["id"]),
        asof=str(asof),
    )


class ConcurrencyError(RuntimeError):
    pass


# ============================================================
# Internal Backend Ports
# ============================================================


class OnLoadCurrent(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
    ) -> CurrentRow | None: ...


class OnLoadCurrentMany(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_ids: Sequence[EntityId],
    ) -> Mapping[EntityId, CurrentRow]: ...


class OnLoadRevisions(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        rev_gt: int,
        ts_lte: datetime,
    ) -> Sequence[RevisionRow]: ...


class OnLoadSnapshot(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        ts_lte: datetime,
    ) -> SnapshotRow | None: ...


class OnAppendRevision(Protocol):
    async def __call__(
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
    ) -> None: ...


class OnUpsertCurrent(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        rev: int,
        data: JsonValue,
        updated_at: datetime,
    ) -> None: ...


class OnWriteSnapshot(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        rev: int,
        ts: datetime,
        data: JsonValue,
    ) -> None: ...


class OnIndexEnsure(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        specs: Sequence[IndexSpec],
    ) -> None: ...


class OnIndexList(Protocol):
    async def __call__(
        self, *, domain_id: DomainId, kind_id: KindId, space_id: SpaceId
    ) -> Sequence[IndexSpec]: ...


class OnIndexReplaceTerms(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        terms: Sequence[IndexTerm],
        written_at: datetime,
    ) -> None: ...


class OnIndexScan(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        index_key: IndexKey,
        mode: ScanMode,
        value: IndexValue | None,
        lo: IndexValue | None,
        hi: IndexValue | None,
        after_value: IndexValue | None,
        after_entity_id: EntityId | None,
        limit: int,
        as_of: datetime,
    ) -> Sequence[tuple[IndexValue, EntityId]]: ...


class OnQueryIndex(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        terms: Sequence[IndexQueryTerm],
        mode: Literal["and", "or"],
        limit: int = 100,
    ) -> list[EntityId]: ...


class OnGC(Protocol):
    async def __call__(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        policy: RetentionPolicy,
        now: datetime,
    ) -> None: ...


class OnGCGlobal(Protocol):
    async def __call__(self, *, policy: RetentionPolicy) -> None: ...
