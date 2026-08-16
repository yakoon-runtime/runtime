from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from y5n.runtime.api.flow.primitives import Control
    from y5n.runtime.api.runtime.invocation import Invocation


class Flow(Protocol):
    """Protocol that all flow implementations must satisfy.

    Defines the minimal interface the scheduler and engine depend on:
    identity (id), execution state (node, control, cursor), scheduling
    flags (scheduled), pipeline chaining, and view/output routing.

    The node attribute is deliberately untyped here: the API describes
    the Flow's shape, not the Node (which is engine-internal).
    """

    id: str
    node: Any
    control: Control | None
    scheduled: bool
    pipeline: Sequence[str | Invocation] | None
    out_channel: str | None
    view: Any | None
    kind: Any
