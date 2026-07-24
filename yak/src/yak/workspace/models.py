from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from yak.distribution.models import PackName


@dataclass
class Workspace:
    path: Path
    distribution: str
    packs: list[PackName] = field(default_factory=list)
    created: datetime | None = None
    updated: datetime | None = None
