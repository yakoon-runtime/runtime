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
    # Output
    WRITE = "write"
    ERROR = "error"
    VIEW = "view"

    # Side effects
    CWD = "cwd"

    # Timer
    DELAY = "delay"
    DELAY_UNTIL = "delay_until"

    # Scheduler / Flow control
    FLOWS_LIST = "flows.list"
    FLOW_STOP = "flow.stop"
    FLOW_FG = "flow.fg"
    FLOW_BG = "flow.bg"

    # Interactive flow — suspend and wait for event
    PROMPT = "prompt"
    RECEIVE = "receive"

    # Event channel — emit event
    SEND = "send"


@dataclass(frozen=True)
class Marker:
    kind: MarkerKind
    value: Any
