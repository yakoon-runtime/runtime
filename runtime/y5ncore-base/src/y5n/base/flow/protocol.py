from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from y5n.base.flow.primitives import Control
    from y5n.base.nodes import Node, Request


class Flow(Protocol):
    """Protocol that all flow implementations must satisfy.

    Defines the minimal interface the scheduler and engine depend on:
    identity (id), execution state (node, control, cursor), scheduling
    flags (scheduled), pipeline chaining, and view/output routing.
    """

    id: str
    node: Node
    control: Control | None
    scheduled: bool
    pipeline: list[str | Request] | None
    out_channel: str | None
    view: Any | None
    kind: Any
