from __future__ import annotations

from enum import StrEnum


class FlowKind(StrEnum):
    """Distinguishes user-facing flows from system-internal flows.

    System flows are scheduled with higher priority by the scheduler.
    """

    USER = "user"
    SYSTEM = "system"
