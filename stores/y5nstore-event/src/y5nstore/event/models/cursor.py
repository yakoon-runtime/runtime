from dataclasses import dataclass
from typing import Any

from .mode import ScanMode


@dataclass(frozen=True, slots=True)
class ScanCursor:
    index_key: str
    mode: ScanMode
    value: Any
    entity_id: str
    asof: str  # ISO timestamp (UTC) (for freeze view)
