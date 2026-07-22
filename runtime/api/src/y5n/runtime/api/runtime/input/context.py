from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Origin(StrEnum):
    """Well-known caller origins for the interaction pipeline."""

    HUMAN = "human"
    AGENT = "agent"
    SCHEDULER = "scheduler"


@dataclass(frozen=True, slots=True)
class InputContext:
    origin: Origin = Origin.HUMAN
    channel: str | None = None
    echo: str | None = None
