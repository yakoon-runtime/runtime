from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar

from .request import DataRequest

T = TypeVar("T")
ReadRow = dict[str, Any]


@dataclass(frozen=True)
class DataResult(Generic[T]):
    rows: list[T]
    meta: dict[str, Any] = field(default_factory=dict)

    def first_or_default(self, default: T | None = None) -> T | None:
        return self.rows[0] if self.rows else default

    def first(self) -> T:
        if not self.rows:
            raise LookupError("DataResult is empty")
        return self.rows[0]

    def one_or_none(self) -> T | None:
        if len(self.rows) > 1:
            raise ValueError("Expected at most one row, got multiple.")
        return self.rows[0] if self.rows else None

    def one(self) -> T:
        if len(self.rows) != 1:
            raise ValueError(f"Expected exactly one row, got {len(self.rows)}.")
        return self.rows[0]

    def is_empty(self) -> bool:
        return not self.rows

    def exists(self) -> bool:
        return bool(self.rows)


class DataSource(Protocol[T]):

    async def read(self, request: DataRequest) -> DataResult[T]: ...


# ----------------------------------
# PORT
# ----------------------------------


class OnDataSource(Protocol):
    async def __call__(
        self,
        request: DataRequest,
    ) -> DataResult: ...


class OnDataBind(Protocol):
    def __call__(self, source: str, provider: DataSource): ...
