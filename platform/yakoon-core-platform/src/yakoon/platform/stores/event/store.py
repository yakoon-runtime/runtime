from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from yakoon.base.ports import EntityStore, IndexRegistry, PatchStrategy
from yakoon.base.stores.event.entity import (
    EntityId,
    GetResult,
    IndexKey,
    IndexTerm,
    JsonValue,
    PluginGroup,
    PutResult,
    RetentionPolicy,
    ScopeId,
    SnapshotHint,
)
from yakoon.platform.stores.event.backend import EntityStoreBackend


class ConcurrencyError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SnapshotPolicy:
    """
    Minimal policy: manual hints + automatic safety net.
    Can be made configurable per scope/plugin_group later.
    """

    every_n_revisions: int = 50
    max_age_seconds: int = 15 * 60  # 15 min


def _utc_now() -> datetime:
    return datetime.now(UTC)


class DefaultEntityStore(EntityStore, IndexRegistry):
    """
    ES-light store semantics:
    - current state is materialized for fast reads
    - revisions store patches (retained 30-90d via GC/partitions)
    - snapshots anchor historical reconstruction
    - index-on-write for queries

    Notes:
    - This class contains NO SQL. It calls a backend that can be memory/sqlite/pg.
    - Patch semantics are injected via PatchStrategy.
    """

    def __init__(
        self,
        *,
        backend: EntityStoreBackend,
        patch_strategy: PatchStrategy,
        snapshot_policy: SnapshotPolicy | None = None,
        enable_revisions: bool = True,
    ) -> None:
        self._backend = backend
        self._patch = patch_strategy
        self._snap = snapshot_policy or SnapshotPolicy()
        self._enable_revisions = enable_revisions

    # ----------------------------
    # IndexRegistry
    # ----------------------------

    async def ensure(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        specs: Sequence,  # Sequence[IndexSpec], keep import light here
    ) -> None:
        async with self._backend.transaction() as tx:
            await tx.index_ensure(
                scope_id=scope_id, plugin_group=plugin_group, specs=specs
            )

    async def list(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
    ) -> Sequence:
        async with self._backend.transaction() as tx:
            return await tx.index_list(scope_id=scope_id, plugin_group=plugin_group)

    # ----------------------------
    # EntityStore
    # ----------------------------

    async def put(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        entity_id: EntityId,
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
        self._patch.validate(patch)
        now = _utc_now()

        async with self._backend.transaction() as tx:
            cur = await tx.load_current(
                scope_id=scope_id, plugin_group=plugin_group, entity_id=entity_id
            )

            if cur is None:
                cur_rev = 0
                cur_state: JsonValue | None = None
                last_snapshot_rev = 0
                last_snapshot_ts: datetime | None = None
            else:
                cur_rev = cur.rev
                cur_state = cur.data
                # backend may expose last snapshot metadata later; for now we re-check via query
                # (you can optimize by keeping snapshot pointers in current row)
                last_snapshot = await tx.load_snapshot_at_or_before(
                    scope_id=scope_id,
                    plugin_group=plugin_group,
                    entity_id=entity_id,
                    ts_lte=now,
                )
                last_snapshot_rev = 0 if last_snapshot is None else last_snapshot.rev
                last_snapshot_ts = None if last_snapshot is None else last_snapshot.ts

            if expected_rev is not None and expected_rev != cur_rev:
                raise ConcurrencyError(
                    f"expected_rev={expected_rev} but current_rev={cur_rev}"
                )

            new_state = self._patch.apply(cur_state, patch)
            new_rev = cur_rev + 1

            if self._enable_revisions:
                await tx.append_revision(
                    scope_id=scope_id,
                    plugin_group=plugin_group,
                    entity_id=entity_id,
                    rev=new_rev,
                    ts=now,
                    patch=patch,
                )

            await tx.upsert_current(
                scope_id=scope_id,
                plugin_group=plugin_group,
                entity_id=entity_id,
                rev=new_rev,
                data=new_state,
                updated_at=now,
            )

            if indexes:
                await tx.index_replace_terms(
                    scope_id=scope_id,
                    plugin_group=plugin_group,
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
                    scope_id=scope_id,
                    plugin_group=plugin_group,
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

    async def get(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        entity_id: EntityId,
        at_time: datetime | None = None,
    ) -> GetResult:
        """
        - at_time=None: return current
        - at_time set: snapshot <= T + apply revisions up to T
        """
        if at_time is None:
            async with self._backend.transaction() as tx:
                cur = await tx.load_current(
                    scope_id=scope_id, plugin_group=plugin_group, entity_id=entity_id
                )
                if cur is None:
                    return GetResult(
                        entity_id=entity_id,
                        data=None,
                        rev=None,
                        as_of=_utc_now(),
                        is_historical=False,
                    )
                return GetResult(
                    entity_id=entity_id,
                    data=cur.data,
                    rev=cur.rev,
                    as_of=cur.updated_at,
                    is_historical=False,
                )

        # historical path
        t = at_time
        async with self._backend.transaction() as tx:
            snap = await tx.load_snapshot_at_or_before(
                scope_id=scope_id,
                plugin_group=plugin_group,
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
                scope_id=scope_id,
                plugin_group=plugin_group,
                entity_id=entity_id,
                rev_gt=base_rev,
                ts_lte=t,
            )

        state = base_state
        last_rev: int | None = None if snap is None else snap.rev
        for r in revs:
            self._patch.validate(r.patch)
            state = self._patch.apply(state, r.patch)
            last_rev = r.rev

        return GetResult(
            entity_id=entity_id,
            data=state,
            rev=last_rev,
            as_of=t,
            is_historical=True,
        )

    async def query(
        self,
        *,
        scope_id: ScopeId,
        plugin_group: PluginGroup,
        index_key: IndexKey,
        value,
        limit: int = 100,
        cursor: str | None = None,
    ):
        async with self._backend.transaction() as tx:
            return await tx.index_query_ids(
                scope_id=scope_id,
                plugin_group=plugin_group,
                index_key=index_key,
                value=value,
                limit=limit,
                cursor=cursor,
            )

    async def gc(
        self,
        *,
        scope_id: ScopeId | None,
        plugin_group: PluginGroup | None,
        policy: RetentionPolicy,
    ) -> None:
        """
        Delegates GC to backend (which may do partition-drop or delete).
        Semantics: remove revisions/snapshots older than policy window(s),
        and clean index rows if needed.
        """
        async with self._backend.transaction() as tx:
            # You will implement backend.gc(...) later; keeping this stubbed is fine.
            await tx.gc(scope_id=scope_id, plugin_group=plugin_group, policy=policy)  # type: ignore[attr-defined]

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
        if snapshot_hint == SnapshotHint.FORCE:
            return True
        if snapshot_hint == SnapshotHint.COMMIT:
            return True
        if snapshot_hint == SnapshotHint.NONE:
            return False

        # AUTO safety nets
        if (new_rev - last_snapshot_rev) >= self._snap.every_n_revisions:
            return True

        if last_snapshot_ts is None:
            # no snapshot yet: don't force immediately; let N handle it
            return False

        age = (now - last_snapshot_ts).total_seconds()
        return age >= self._snap.max_age_seconds
