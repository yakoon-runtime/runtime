from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from y5n.base.flow.primitives import Control
from y5n.base.runtime import Event

if TYPE_CHECKING:
    from y5n.base.nodes import Node
    from y5n.base.projection import Projection

from .cursor import FlowCursor
from .types import FlowKind


@dataclass
class Flow:
    id: str

    node: Node
    event: Event
    cursor: FlowCursor
    tokens: list[str] | None = None
    control: Control | None = None
    view: Projection | None = None

    scheduled: bool = False
    wake_at: float | None = None
    kind: FlowKind = FlowKind.USER

    pipeline: list[str] | None = None
    out_channel: str | None = None

    def has_stack(self):
        return self.cursor.has_stack()
