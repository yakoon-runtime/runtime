from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from y5n.runtime.engine.runtime.input.context import InputContext

from ..model import DocumentHeader
from .patch import Patch


@dataclass(frozen=True, slots=True)
class DocumentState:
    user: str | None = None
    node_path: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentEvent:
    """
    Unified transport envelope for hosts.

    Hosts always receive the same kind of event:
     - optional header update
     - patch payload for body mutation
    Typical usage:
     - begin_document(...)  -> header + reset patch
     - emit_block(...)  -> patch only
     - finish_document(...) -> final patch only
    """

    kind: Literal["view_event"] = "view_event"
    id: str = ""
    header: DocumentHeader | None = None
    ctx: InputContext | None = None
    state: DocumentState | None = None

    job_id: str = "system"
    view_params: dict | None = None
    patch: Patch = field(default_factory=Patch)

    def is_final(self) -> bool:
        return self.patch.final
