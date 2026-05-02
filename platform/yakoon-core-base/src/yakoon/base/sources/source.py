from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Literal, Protocol, TypeVar

from .request import DataRequest

T = TypeVar("T")
ReadRow = dict[str, Any]

Status = Literal["ok", "not_found", "denied", "invalid"]


@dataclass(frozen=True)
class DataResult(Generic[T]):
    rows: list[T]
    status: Status
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.status in ("not_found", "denied") and self.rows:
            raise ValueError("rows must be empty when status is not_found or denied")

    @classmethod
    def ok(cls, rows: list[T], **meta) -> DataResult[T]:
        return cls(rows=rows, status="ok", meta=meta)

    @classmethod
    def not_found(cls, **meta) -> DataResult[T]:
        return cls(rows=[], status="not_found", meta=meta)

    @classmethod
    def denied(cls, **meta) -> DataResult[T]:
        return cls(rows=[], status="denied", meta=meta)

    @classmethod
    def invalid(cls, **meta) -> DataResult[T]:
        return cls(rows=[], status="invalid", meta=meta)

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

    def is_ok(self) -> bool:
        return self.status == "ok"

    def exists(self) -> bool:
        return self.status == "ok" and bool(self.rows)

    def is_empty(self) -> bool:
        return self.status == "ok" and not self.rows


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
