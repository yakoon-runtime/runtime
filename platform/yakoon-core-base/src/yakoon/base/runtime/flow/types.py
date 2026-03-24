from __future__ import annotations

from enum import StrEnum


class FlowKind(StrEnum):
    USER = "user"  # sichtbare Jobs
    SYSTEM = "system"  # interne Flows (z.B. jobs, assistant intern)


class FlowState(StrEnum):
    READY = "READY"
    SLEEPING = "SLEEPING"
    WAITING_INPUT = "WAITING_INPUT"
