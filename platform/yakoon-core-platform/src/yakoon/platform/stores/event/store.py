from __future__ import annotations

import base64
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from yakoon.base.models.key import Key
from yakoon.base.models.ns import Namespace
from yakoon.base.ports import EntityStore, IndexRegistry, PatchStrategy
from yakoon.base.stores.event.entity import (
    DomainId,
    EntityId,
    GetResult,
    IndexKey,
    IndexSpec,
    IndexTerm,
    IndexValue,
    JsonValue,
    KindId,
    PatchFormat,
    PutResult,
    RetentionPolicy,
    SnapshotHint,
    SpaceId,
)
from yakoon.platform.stores.event.backend import EntityStoreBackend, RevisionRow


class ConcurrencyError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ScanCursor:
    index_key: str
    mode: str  # "eq" | "range"
    value: Any
    entity_id: str


@dataclass(frozen=True, slots=True)
class SnapshotPolicy:
    """
    Minimal policy: manual hints + automatic safety net.
    Can be made configurable per namespace later.
    """

    every_n_revisions: int = 20
    max_age_seconds: int = 15  # 15x5 min


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _ns_kind(ns: Namespace) -> str:
    return getattr(ns, "kind", ns.kind)  # compat


def _ns_space(ns: Namespace) -> str:
    return getattr(ns, "space", ns.space)  # compat


def _dims_from_namespace(ns: Namespace) -> tuple[DomainId, KindId, SpaceId]:
    return (DomainId(ns.domain), KindId(_ns_kind(ns)), SpaceId(_ns_space(ns)))


def _dims_from_key(key: Key) -> tuple[DomainId, KindId, SpaceId, EntityId]:
    d, k, s = _dims_from_namespace(key.namespace)
    return (d, k, s, EntityId(key.id))


class DefaultEntityStore(EntityStore, IndexRegistry):
    """
    ES-light store semantics:
    - current state is materialized for fast reads
    - revisions store patches (retained via GC)
    - snapshots anchor historical reconstruction
    - index-on-write for queries

    Backend is pure persistence (no Namespace/Key logic).
    Patch semantics are injected via PatchStrategy.
    """

    def __init__(
        self,
        *,
        backend: EntityStoreBackend,
        writer: PatchStrategy,
        readers: Mapping[PatchFormat, PatchStrategy],
        snapshot_policy: SnapshotPolicy | None = None,
        enable_revisions: bool = True,
    ) -> None:
        self._backend = backend
        self._writer = writer
        self._readers = dict(readers)
        self._readers.setdefault(writer.format, writer)
        self._snap = snapshot_policy or SnapshotPolicy()
        self._enable_revisions = enable_revisions

    # ----------------------------
    # IndexRegistry
    # ----------------------------

    async def ensure(
        self,
        *,
        namespace: Namespace,
        specs: Sequence[IndexSpec],
    ) -> None:
        domain_id, kind_id, space_id = _dims_from_namespace(namespace)
        async with self._backend.transaction() as tx:
            await tx.index_ensure(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
                specs=specs,
            )

    async def list(
        self,
        *,
        namespace: Namespace,
    ) -> Sequence[IndexSpec]:
        domain_id, kind_id, space_id = _dims_from_namespace(namespace)
        async with self._backend.transaction() as tx:
            return await tx.index_list(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
            )

    # ----------------------------
    # EntityStore
    # ----------------------------

    async def put(
        self,
        *,
        key: Key,
        patch: JsonValue,
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, object] | None = None,  # kept for future use
        expected_rev: int | None = None,
    ) -> PutResult:
        """
        Write flow (single tx):
          - load current
          - check expected_rev (optional)
          - apply patch => new_state
          - next_rev = current.rev + 1 (or 1)
          - append revision (optional)
          - upsert current
          - replace index terms for provided keys
          - maybe write snapshot
        """
        _ = meta  # reserved
        self._writer.validate(patch)
        now = _utc_now()

        domain_id, kind_id, space_id, entity_id = _dims_from_key(key)

        async with self._backend.transaction() as tx:
            cur = await tx.load_current(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
                entity_id=entity_id,
            )

            if cur is None:
                cur_rev = 0
                cur_state: JsonValue | None = None
                last_snapshot_rev = 0
                last_snapshot_ts: datetime | None = None
            else:
                cur_rev = cur.rev
                cur_state = cur.data
                last_snapshot = await tx.load_snapshot_at_or_before(
                    domain_id=domain_id,
                    kind_id=kind_id,
                    space_id=space_id,
                    entity_id=entity_id,
                    ts_lte=now,
                )
                last_snapshot_rev = 0 if last_snapshot is None else last_snapshot.rev
                last_snapshot_ts = None if last_snapshot is None else last_snapshot.ts

            if expected_rev is not None and expected_rev != cur_rev:
                raise ConcurrencyError(
                    f"expected_rev={expected_rev} but current_rev={cur_rev}"
                )

            patch_format = self._writer.format
            strat = self._readers[patch_format]
            new_state = strat.apply(current=cur_state, patch=patch)
            new_rev = cur_rev + 1

            if self._enable_revisions:
                await tx.append_revision(
                    domain_id=domain_id,
                    kind_id=kind_id,
                    space_id=space_id,
                    entity_id=entity_id,
                    rev=new_rev,
                    ts=now,
                    patch_format=patch_format,
                    patch=patch,
                )

            await tx.upsert_current(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
                entity_id=entity_id,
                rev=new_rev,
                data=new_state,
                updated_at=now,
            )

            if indexes:
                await tx.index_replace_terms(
                    domain_id=domain_id,
                    kind_id=kind_id,
                    space_id=space_id,
                    entity_id=entity_id,
                    terms=indexes,
                )

            snapshot_written = False
            if await self._should_snapshot(
                snapshot_hint=snapshot_hint,
                new_rev=new_rev,
                last_snapshot_rev=last_snapshot_rev,
                now=now,
                last_snapshot_ts=last_snapshot_ts,
            ):
                await tx.write_snapshot(
                    domain_id=domain_id,
                    kind_id=kind_id,
                    space_id=space_id,
                    entity_id=entity_id,
                    rev=new_rev,
                    ts=now,
                    data=new_state,
                )
                snapshot_written = True

            return PutResult(
                entity_id=entity_id,
                rev=new_rev,
                updated_at=now,
                snapshot_written=snapshot_written,
            )

    async def put_doc(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, Any] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult:
        """
        Full replace semantics:
        The stored document becomes exactly `doc`.
        """
        current = None

        if expected_rev is not None:
            cur = await self.get_one(key=key)
            if cur.rev != expected_rev:
                raise RuntimeError(
                    f"Optimistic lock failed for {key}: "
                    f"expected_rev={expected_rev}, actual_rev={cur.rev}"
                )
            current = cur.data

        patch = self._writer.create_full_replace(
            current=current,
            new_doc=doc,
        )

        return await self.put(
            key=key,
            patch=patch,
            indexes=indexes,
            snapshot_hint=snapshot_hint,
            meta=meta,
            expected_rev=expected_rev,
        )

    async def put_fields(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, Any] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult:
        """
        Partial update semantics:
        Only provided fields are modified.
        """
        current = None

        if expected_rev is not None:
            cur = await self.get_one(key=key)
            if cur.rev != expected_rev:
                raise RuntimeError(
                    f"Optimistic lock failed for {key}: "
                    f"expected_rev={expected_rev}, actual_rev={cur.rev}"
                )
            current = cur.data

        patch = self._writer.create_partial_update(
            current=current,
            fields=doc,
        )

        return await self.put(
            key=key,
            patch=patch,
            indexes=indexes,
            snapshot_hint=snapshot_hint,
            meta=meta,
            expected_rev=expected_rev,
        )

    async def delete_fields(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, Any] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult:
        """
        Delete semantics:
        Removes the given top-level field names from the document.
        Keys of `doc` are interpreted as field names to delete.
        """
        current = None

        if expected_rev is not None:
            cur = await self.get_one(key=key)
            if cur.rev != expected_rev:
                raise RuntimeError(
                    f"Optimistic lock failed for {key}: "
                    f"expected_rev={expected_rev}, actual_rev={cur.rev}"
                )
            current = cur.data

        patch = self._writer.create_delete(
            current=current,
            fields=list(doc.keys()),
        )

        return await self.put(
            key=key,
            patch=patch,
            indexes=indexes,
            snapshot_hint=snapshot_hint,
            meta=meta,
            expected_rev=expected_rev,
        )

    async def get_one(
        self,
        *,
        key: Key,
        at_time: datetime | None = None,
    ) -> GetResult:
        """
        - at_time=None: return current
        - at_time set: snapshot <= T + apply revisions up to T
        """
        domain_id, kind_id, space_id, entity_id = _dims_from_key(key)

        if at_time is None:
            async with self._backend.transaction() as tx:
                cur = await tx.load_current(
                    domain_id=domain_id,
                    kind_id=kind_id,
                    space_id=space_id,
                    entity_id=entity_id,
                )
                if cur is None:
                    return GetResult(
                        entity_id=entity_id,
                        data=None,
                        rev=None,
                        as_of=_utc_now(),
                        historical=False,
                    )
                return GetResult(
                    entity_id=entity_id,
                    data=cur.data,
                    rev=cur.rev,
                    as_of=cur.updated_at,
                    historical=False,
                )

        # historical path
        t = at_time
        async with self._backend.transaction() as tx:
            snap = await tx.load_snapshot_at_or_before(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
                entity_id=entity_id,
                ts_lte=t,
            )
            if snap is None:
                base_state: JsonValue | None = None
                base_rev = 0
            else:
                base_state = snap.data
                base_rev = snap.rev

            revs = await tx.load_revisions(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
                entity_id=entity_id,
                rev_gt=base_rev,
                ts_lte=t,
            )

        state = base_state
        last_rev: int | None = None if snap is None else snap.rev
        for r in revs:
            strat = self._readers.get(r.patch_format)
            if strat is None:
                raise RuntimeError(
                    f"No patch reader registered for format={r.patch_format}"
                )
            state = strat.apply(current=state, patch=r.patch)
            last_rev = r.rev

        return GetResult(
            entity_id=entity_id,
            data=state,
            rev=last_rev,
            as_of=t,
            historical=True,
        )

    async def get_many(
        self,
        *,
        keys: Sequence[Key],
    ) -> list[GetResult]:

        if not keys:
            return []

        # Gruppierung nach Namespace-Dimension
        groups: dict[tuple[DomainId, KindId, SpaceId], list[tuple[int, EntityId]]] = (
            defaultdict(list)
        )

        for idx, key in enumerate(keys):
            domain_id, kind_id, space_id, entity_id = _dims_from_key(key)
            groups[(domain_id, kind_id, space_id)].append((idx, entity_id))

        # Platzhalter-Liste (gleiche Reihenfolge wie Input!)
        results: list[GetResult | None] = [None] * len(keys)

        now = _utc_now()

        async with self._backend.transaction() as tx:
            for (domain_id, kind_id, space_id), items in groups.items():

                eids = [eid for _, eid in items]

                rows = await tx.load_current_many(
                    domain_id=domain_id,
                    kind_id=kind_id,
                    space_id=space_id,
                    entity_ids=eids,
                )

                for idx, eid in items:
                    row = rows.get(eid)
                    if row is None:
                        results[idx] = GetResult(
                            entity_id=eid,
                            data=None,
                            rev=None,
                            as_of=now,
                            historical=False,
                        )
                    else:
                        results[idx] = GetResult(
                            entity_id=eid,
                            data=row.data,
                            rev=row.rev,
                            as_of=row.updated_at,
                            historical=False,
                        )

        # type narrowing
        return [r for r in results if r is not None]

    async def scan(
        self,
        *,
        namespace: Namespace,
        index_key: IndexKey,
        value: IndexValue | None = None,
        lo: IndexValue | None = None,
        hi: IndexValue | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[Key], str | None]:

        domain_id = DomainId(namespace.domain)
        kind_id = KindId(namespace.kind)
        space_id = SpaceId(namespace.space)

        mode = "eq" if value is not None else "range"

        after_value = None
        after_entity_id = None

        if cursor:
            c = decode_cursor(cursor)

            if c.index_key != str(index_key) or c.mode != mode:
                raise ValueError("cursor does not match scan parameters")

            after_value = c.value
            after_entity_id = EntityId(c.entity_id)

        async with self._backend.transaction() as tx:

            rows = await tx.index_scan(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
                index_key=index_key,
                mode=mode,
                value=value,
                lo=lo,
                hi=hi,
                after_value=after_value,
                after_entity_id=after_entity_id,
                limit=limit,
            )

        keys: list[Key] = []
        next_cursor: str | None = None

        for v, eid in rows:
            keys.append(
                Key.from_parts(
                    domain=namespace.domain,
                    kind=namespace.kind,
                    space=namespace.space,
                    id=str(eid),
                )
            )

        if rows:
            last_value, last_id = rows[-1]

            next_cursor = encode_cursor(
                ScanCursor(
                    index_key=str(index_key),
                    mode=mode,
                    value=last_value,
                    entity_id=str(last_id),
                )
            )

        return keys, next_cursor

    async def gc(
        self,
        *,
        namespace: Namespace,
        policy: RetentionPolicy,
    ) -> None:
        domain_id, kind_id, space_id = _dims_from_namespace(namespace)
        async with self._backend.transaction() as tx:
            await tx.gc(
                domain_id=domain_id,
                kind_id=kind_id,
                space_id=space_id,
                policy=policy,
                now=_utc_now(),
            )

    # ----------------------------
    # Snapshot decision
    # ----------------------------

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

    def _apply_revisions(
        self,
        *,
        base: JsonValue | None,
        revisions: list[RevisionRow],
    ) -> JsonValue | None:
        cur = base
        for r in revisions:
            strat = self._readers.get(r.patch_format)
            if strat is None:
                raise RuntimeError(f"No patch reader for format={r.patch_format}")
            cur = strat.apply(current=cur, patch=r.patch)
        return cur


def encode_cursor(c: ScanCursor) -> str:
    raw = json.dumps(
        {"ik": c.index_key, "m": c.mode, "v": c.value, "id": c.entity_id},
        separators=(",", ":"),
    ).encode("utf-8")

    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> ScanCursor:
    pad = "=" * (-len(cursor) % 4)
    raw = base64.urlsafe_b64decode((cursor + pad).encode("ascii"))

    obj = json.loads(raw.decode("utf-8"))

    return ScanCursor(
        index_key=obj["ik"],
        mode=obj["m"],
        value=obj["v"],
        entity_id=obj["id"],
    )
