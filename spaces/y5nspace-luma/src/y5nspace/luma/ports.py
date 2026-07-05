from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from y5n.api.naming import Key, Namespace
from y5nstore.event.models import (
    GetResult,
    IndexQueryTerm,
    IndexSpec,
    PutResult,
    SnapshotHint,
)


class OnGet(Protocol):
    async def __call__(self, *, key: Key, snapshot: SnapshotHint | None = None) -> GetResult | None: ...


class OnGetMany(Protocol):
    async def __call__(self, *, keys: Sequence[Key]) -> list[GetResult | None]: ...


class OnAppend(Protocol):
    async def __call__(self, *, key: Key, value: dict, snapshot: SnapshotHint | None = None) -> PutResult: ...


class OnReplace(Protocol):
    async def __call__(self, *, key: Key, value: dict) -> PutResult: ...


class OnScan(Protocol):
    async def __call__(self, *, namespace: Namespace) -> list[GetResult]: ...


class OnDelete(Protocol):
    async def __call__(self, *, key: Key) -> None: ...


class OnQueryIndex(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        terms: Sequence[IndexQueryTerm],
        mode: str,
        limit: int = 100,
    ) -> tuple[list[Key], str | None]: ...


class OnEnsureIndexes(Protocol):
    async def __call__(self, *, namespace: Namespace, specs: Sequence[IndexSpec]) -> None: ...
