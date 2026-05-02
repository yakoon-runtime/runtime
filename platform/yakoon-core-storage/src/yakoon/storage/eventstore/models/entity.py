from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import (
    Literal,
    NewType,
    TypeAlias,
)


class PatchFormat(StrEnum):
    JSONPATCH = "jsonpatch"
    FASTPATCH = "fastpatch"


# ----------------------------
# JSON (for entity payloads, patches, snapshots)
# ----------------------------

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonPrimitive | dict[str, "JsonValue"] | list["JsonValue"]

# ----------------------------
# Strong-ish identifiers
# ----------------------------

SpaceId = NewType("SpaceId", str)
DomainId = NewType("DomainId", str)
KindId = NewType("KindId", str)
EntityId = NewType("EntityId", str)

IndexKey = NewType("IndexKey", str)

# Index values should be strictly comparable/scalar
IndexValue: TypeAlias = str | int | float | bool


# ----------------------------
# Index model
# ----------------------------


class ValueType(StrEnum):
    TEXT = "text"
    INT = "int"
    BOOL = "bool"
    FLOAT = "float"
    TIME = "time"  # typically stored normalized (e.g. ISO UTC string or epoch)
    UUID = "uuid"


@dataclass(frozen=True, slots=True)
class IndexSpec:
    """
    Declares a secondary index needed by a domain_id inside a space.
    This is structural metadata, created/ensured at plugin load time.
    """

    key: IndexKey
    value_type: ValueType
    unique: bool = False
    retention_days: int | None = None  # optional: if index data has its own TTL

    # TODO: Nachdenke, ob wir index sharding verwenden. um statt
    # 1 Bucket -> 100000 Records 16 Buckets -> je ~6000 Records zu erhalten.
    shard_count: int | None = 1


@dataclass(frozen=True, slots=True)
class IndexTerm:
    """
    A concrete index value written alongside an entity update (index-on-write).
    """

    key: IndexKey
    value: IndexValue


# ----------------------------
# Snapshot & retention model
# ----------------------------


class SnapshotHint(StrEnum):
    NONE = "none"
    AUTO = "auto"  # let store policy decide
    COMMIT = "commit"  # business boundary (CommandFinished / InputCompleted)
    FORCE = "force"  # always write a snapshot


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """
    GC policy; typically configurable per (space_id, domain_id) and optionally
    further per namespace/index key in your config layer.
    """

    keep_revisions_days: int  # e.g. 30..90
    keep_snapshots_days: int | None = None
    snapshot_granularity: Literal["none", "hour", "day", "week"] | None = "day"


# ----------------------------
# Store I/O models
# ----------------------------


@dataclass(frozen=True, slots=True)
class PutResult:
    entity_id: EntityId
    rev: int
    updated_at: datetime
    snapshot_written: bool


@dataclass(frozen=True, slots=True)
class GetResult:
    entity_id: EntityId
    data: (
        JsonValue | None
    )  # None => not found (or tombstoned, depending on your semantics)
    rev: int | None
    as_of: datetime
    historical: bool

    # Backward-compat alias (older code may still read .is_historical)
    @property
    def is_historical(self) -> bool:
        return self.historical
