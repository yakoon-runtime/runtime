from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .document import ViewHeader
from .patch import PatchSpec


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
    patch: PatchSpec = field(default_factory=PatchSpec)
