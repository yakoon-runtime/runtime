from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .patch import Patch
from .view import ViewHeader


@dataclass(frozen=True, slots=True)
class ViewEvent:
    """
    Unified transport envelope for hosts.

    Hosts always receive the same kind of event:
     - optional header update
     - patch payload for body mutation
     Typical usage:
     - begin_view(...)  -> header + reset patch
     - emit_block(...)  -> patch only
     - finish_view(...) -> final patch only
    """

    kind: Literal["view_event"] = "view_event"
    id: str = ""
    header: ViewHeader | None = None
    patch: Patch = field(default_factory=Patch)
    meta: dict = field(default_factory=dict)

    channel: str = "main"
    job_id: str = "system"

    def is_final(self) -> bool:
        return self.patch.final
