from __future__ import annotations

from collections.abc import Sequence
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


@dataclass(frozen=True, slots=True)
class SnapshotRow:
    entity_id: EntityId
    rev: int
    ts: datetime
    data: JsonValue


class EntityStoreBackendTx(Protocol):

    async def __aenter__(self) -> EntityStoreBackendTx: ...
    async def __aexit__(self, exc_type, exc, tb) -> bool | None: ...

    async def load_current(
        self,
        *,
        domain_id: DomainId,
        space_id: SpaceId,
        entity_id: EntityId,
    ) -> CurrentRow | None: ...

    async def upsert_current(
        self,
        *,
        domain_id: DomainId,
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
        space_id: SpaceId,
        entity_id: EntityId,
        rev: int,
        ts: datetime,
        patch: JsonValue,
    ) -> None: ...

    async def load_revisions(
        self,
        *,
        domain_id: DomainId,
        space_id: SpaceId,
        entity_id: EntityId,
        rev_gt: int,
        ts_lte: datetime,
    ) -> Sequence[RevisionRow]: ...

    async def load_snapshot_at_or_before(
        self,
        *,
        domain_id: DomainId,
        space_id: SpaceId,
        entity_id: EntityId,
        ts_lte: datetime,
    ) -> SnapshotRow | None: ...

    async def write_snapshot(
        self,
        *,
        domain_id: DomainId,
        space_id: SpaceId,
        entity_id: EntityId,
        rev: int,
        ts: datetime,
        data: JsonValue,
    ) -> None: ...

    async def index_replace_terms(
        self,
        *,
        domain_id: DomainId,
        space_id: SpaceId,
        entity_id: EntityId,
        terms: Sequence[IndexTerm],
    ) -> None:
        """
        Replace (upsert) index terms for this entity.
        Typically: delete existing rows for (entity_id, keys in terms), then insert.
        """
        ...

    async def index_query_ids(
        self,
        *,
        domain_id: DomainId,
        space_id: SpaceId,
        index_key: IndexKey,
        value: IndexValue,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[EntityId], str | None]: ...

    async def index_ensure(
        self,
        *,
        domain_id: DomainId,
        space_id: SpaceId,
        specs: Sequence[IndexSpec],
    ) -> None: ...

    async def index_list(
        self,
        *,
        domain_id: DomainId,
        space_id: SpaceId,
    ) -> Sequence[IndexSpec]: ...


class EntityStoreBackend(Protocol):

    def transaction(self) -> EntityStoreBackendTx:
        """
        Returns a transactional context object.
        Your implementation can return an async context manager if you prefer:

            async with backend.transaction() as tx: ...
        """
        ...
