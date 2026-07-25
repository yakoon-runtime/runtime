"""Runtime Bus message types.

Each message is a dataclass. The bus routes by type.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum, auto


class Placement(StrEnum):
    """Where to register a provider in the tree.

    SELF    → at the caller's node       (classic provide)
    PARENT  → one level up               (classic publish)
    ROOT    → system-wide                (classic promote)
    """

    SELF = auto()
    PARENT = auto()
    ROOT = auto()


@dataclass
class RegisterProvider:
    provider_id: str
    exports: dict[str, Sequence[str]]
    service: dict | None = None
    placement: Placement = Placement.SELF
    caller_path: str | None = None


@dataclass
class UnregisterProvider:
    provider_id: str


@dataclass
class Ok:
    pass
