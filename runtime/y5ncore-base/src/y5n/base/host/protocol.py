"""
Marker protocol — the contract between SDK and host driver.

Each SDK capability yields a ``Marker`` to the host.  The host
dispatches on ``marker.kind`` and processes ``marker.value``.

This is the one central definition of the language that every
host (runtime, thread, process, …) and every SDK (Python, JS, …)
speaks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class MarkerKind(StrEnum):
    WRITE = "write"
    ERROR = "error"
    DELAY = "delay"
    DELAY_UNTIL = "delay_until"
    VIEW = "view"
    CWD = "cwd"


@dataclass(frozen=True)
class Marker:
    kind: MarkerKind
    value: Any
