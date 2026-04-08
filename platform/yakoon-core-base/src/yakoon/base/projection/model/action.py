from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Action:
    id: str | None = None
    label: str = ""
    command: str | None = None
    payload: dict[str, Any] | None = None
