from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from yakoon.storage.eventstore.models.entity import (
    EntityId,
    JsonValue,
    PatchFormat,
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
