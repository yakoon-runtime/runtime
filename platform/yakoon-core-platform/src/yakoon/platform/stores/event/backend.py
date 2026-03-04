from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

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
)


@dataclass(frozen=True, slots=True)
class CurrentRow:
    entity_id: EntityId
    rev: int
    data: JsonValue
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class RevisionRow:
    entity_id: EntityId
    rev: int
    ts: datetime
    patch: JsonValue
    patch_format: PatchFormat


@dataclass(frozen=True, slots=True)
class SnapshotRow:
    entity_id: EntityId
    rev: int
    ts: datetime
    data: JsonValue


class EntityStoreBackendTx(Protocol):
    async def __aenter__(self) -> EntityStoreBackendTx: ...
    async def __aexit__(self, exc_type, exc, tb) -> bool | None: ...

    # --- entity materialization ---

    async def load_current(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
    ) -> CurrentRow | None: ...

    async def load_current_many(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_ids: Sequence[EntityId],
    ) -> Mapping[EntityId, CurrentRow]: ...

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
    ) -> None: ...

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
    ) -> None: ...

    async def load_revisions(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        rev_gt: int,
        ts_lte: datetime,
    ) -> Sequence[RevisionRow]: ...

    async def load_snapshot_at_or_before(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        ts_lte: datetime,
    ) -> SnapshotRow | None: ...

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
    ) -> None: ...

    # --- index structures & data ---

    async def index_ensure(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        specs: Sequence[IndexSpec],
    ) -> None: ...

    async def index_list(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
    ) -> Sequence[IndexSpec]: ...

    async def index_replace_terms(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        entity_id: EntityId,
        terms: Sequence[IndexTerm],
    ) -> None: ...

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
        """
        Returns ordered (value, entity_id) pairs.
        Order must be (value, entity_id).
        """
        ...

    # --- maintenance ---

    async def gc(
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
        policy: RetentionPolicy,
        now: datetime,
    ) -> None: ...


class EntityStoreBackend(Protocol):
    def transaction(self) -> EntityStoreBackendTx: ...
