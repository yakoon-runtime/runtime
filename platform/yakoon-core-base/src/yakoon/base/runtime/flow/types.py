from __future__ import annotations

from enum import StrEnum


class FlowKind(StrEnum):
    USER = "user"  # sichtbare Jobs
    SYSTEM = "system"  # interne Flows (z.B. jobs, assistant intern)
