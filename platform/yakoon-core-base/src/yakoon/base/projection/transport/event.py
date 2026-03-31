from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ..model import ProjectionHeader
from .patch import Patch


@dataclass(frozen=True, slots=True)
class ProjectionEvent:
    """
    Unified transport envelope for hosts.

    Hosts always receive the same kind of event:
     - optional header update
     - patch payload for body mutation
     Typical usage:
     - begin_projection(...)  -> header + reset patch
     - emit_block(...)  -> patch only
     - finish_projection(...) -> final patch only
    """

    kind: Literal["view_event"] = "view_event"
    id: str = ""
    header: ProjectionHeader | None = None
    patch: Patch = field(default_factory=Patch)
    meta: dict = field(default_factory=dict)

    channel: str = "main"
    job_id: str = "system"

    def is_final(self) -> bool:
        return self.patch.final
