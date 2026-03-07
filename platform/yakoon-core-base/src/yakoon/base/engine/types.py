from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CommandDispatch:
    text: str
    batch_id: str | None = None


@dataclass(frozen=True)
class ResolveDispatch:
    values: dict[str, Any]
    batch_id: str | None = None


DispatchInput = CommandDispatch | ResolveDispatch
