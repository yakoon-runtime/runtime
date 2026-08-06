from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from y5n.runtime.api.flow.primitives import (
    Background,
    Control,
    Effect,
    EmitView,
    Foreground,
    Pulse,
)
from y5n.runtime.api.runtime import Event

if TYPE_CHECKING:
    from y5n.runtime.api.nodes import Invocation, Node

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
    invocation: dict[str, Any] | None = None
    control: Control | None = None
    view: Any = None

    has_output: bool = False

    scheduled: bool = False
    wake_at: float | None = None
    kind: FlowKind = FlowKind.USER

    pipeline: Sequence[str | Invocation] | None = None
    out_channel: str | None = None

    error_depth: int = 0
    """How many consecutive error routes this flow has taken.

    Guards the recursion baseline: the first exception routes to the
    error node; a second one (the error node itself failed) terminates
    at the boot fallback.
    """

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
        return Pulse(effects=effects)

    def deactivate(self):
        """Remove this flow from the foreground."""
        effects = [Background()]
        return Pulse(effects=effects)
