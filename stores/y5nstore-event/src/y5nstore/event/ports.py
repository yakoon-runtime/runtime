from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Literal, Protocol

from .models import (
    CurrentRow,
    DomainId,
    EntityId,
    IndexKey,
    IndexQueryTerm,
    IndexSpec,
    IndexTerm,
    IndexValue,
    JsonValue,
    KindId,
    PatchFormat,
    RetentionPolicy,
    RevisionRow,
    ScanMode,
    SnapshotRow,
    SpaceId,
)


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
        self,
        *,
        domain_id: DomainId,
        kind_id: KindId,
        space_id: SpaceId,
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
    async def __call__(
        self,
        *,
        policy: RetentionPolicy,
    ) -> None: ...
