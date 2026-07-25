"""Flow — read-only snapshot of the current invocation's flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Flow:
    id: str = ""
    key: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Flow:
        return cls(
            id=data.get("id", ""),
            key=data.get("key", ""),
        )
