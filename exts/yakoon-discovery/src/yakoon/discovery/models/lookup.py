from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LookupCandidatesPayload:
    query: str
    candidates: list[Mapping[str, Any]]
    created_at: float
    ttl_seconds: int = 120
