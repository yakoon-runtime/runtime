from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from y5n.base.flow.primitives import (
    Background,
    Control,
    Effect,
    EmitView,
    Foreground,
    Outcome,
)
from y5n.base.runtime import Event

if TYPE_CHECKING:
    from y5n.base.nodes import Node, Request
    from y5n.base.projection import Projection

from .cursor import FlowCursor
from .types import FlowKind


@dataclass(slots=True)
class Flow:
    """Runtime representation of an executing flow.

    Carries the node, event, cursor, control state, and scheduling metadata
    (wake_at, scheduled, pipeline, out_channel).
    """

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

    pipeline: Sequence[str | Request] | None = None
    out_channel: str | None = None

    def has_stack(self):
        return self.cursor.has_stack()

    def activate(self):
        """Bring this flow to the foreground and restore its view."""
        if self.control:
            self.control = self.control.on_activate()

        effects: list[Effect] = [Foreground(flow_id=self.id)]
        if self.view:
            effects.append(
                EmitView(
                    self.view,
                    job_id=self.id,
                    ctx=self.event.context,
                )
            )
        return Outcome(effects=effects)

    def deactivate(self):
        """Remove this flow from the foreground."""
        effects = [Background()]
        return Outcome(effects=effects)
