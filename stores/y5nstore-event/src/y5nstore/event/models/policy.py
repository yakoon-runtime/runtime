from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SnapshotPolicy:
    """
    Minimal policy: manual hints + automatic safety net.
    Can be made configurable per namespace later.
    """

    every_n_revisions: int = 20
    max_age_seconds: int = 15  # 15x5 min
