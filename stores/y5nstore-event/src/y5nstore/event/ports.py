from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from y5n.base.naming import Key, Namespace

from .models import (
    GetResult,
    IndexKey,
    IndexQueryTerm,
    IndexSpec,
    IndexTerm,
    IndexValue,
    PutResult,
    SnapshotHint,
)


class OnGet(Protocol):
    async def __call__(
        self, *, key: Key, snapshot: SnapshotHint | None = None
    ) -> GetResult | None: ...


class OnGetMany(Protocol):
    async def __call__(self, *, keys: Sequence[Key]) -> list[GetResult | None]: ...


class OnReplace(Protocol):
    async def __call__(
        self, *, key: Key, value: dict, indexes: Sequence[IndexTerm] = ()
    ) -> PutResult: ...


class OnDelete(Protocol):
    async def __call__(self, *, key: Key) -> PutResult: ...


class OnAppend(Protocol):
    async def __call__(
        self, *, key: Key, patch: dict, snapshot_hint: SnapshotHint = SnapshotHint.AUTO
    ) -> PutResult: ...


class OnEnsureIndexes(Protocol):
    async def __call__(
        self, *, namespace: Namespace, specs: Sequence[IndexSpec]
    ) -> None: ...


class OnQueryIndex(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        terms: Sequence[IndexQueryTerm],
        mode: str,
        limit: int = 100,
    ) -> tuple[list[Key], str | None]: ...


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
    ) -> tuple[list[Key], str | None]: ...
