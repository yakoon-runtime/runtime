from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Literal, Protocol

from y5n.runtime.api.naming import Key, Namespace

from .models import (
    GetResult,
    IndexKey,
    IndexQueryTerm,
    IndexSpec,
    IndexTerm,
    IndexValue,
    JsonValue,
    PutResult,
    SnapshotHint,
)


class OnGet(Protocol):
    async def __call__(
        self, *, key: Key, at_time: datetime | None = None
    ) -> GetResult: ...


class OnGetMany(Protocol):
    async def __call__(self, *, keys: Sequence[Key]) -> list[GetResult]: ...


class OnAppend(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        patch: JsonValue,
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, object] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult: ...


class OnReplace(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        expected_rev: int | None = None,
    ) -> PutResult: ...


class OnDelete(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        meta: Mapping[str, object] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult: ...


class OnScan(Protocol):
    async def __call__(
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
    ) -> tuple[list[Key], str | None]: ...


class OnQueryIndex(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        terms: Sequence[IndexQueryTerm],
        mode: Literal["and", "or"],
        limit: int = 100,
    ) -> tuple[list[Key], str | None]: ...


class OnEnsureIndexes(Protocol):
    async def __call__(
        self, *, namespace: Namespace, specs: Sequence[IndexSpec]
    ) -> None: ...
