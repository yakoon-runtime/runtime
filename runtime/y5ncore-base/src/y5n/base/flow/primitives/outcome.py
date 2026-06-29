from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .control import Control
from .effect import Effect

if TYPE_CHECKING:
    from y5n.base.nodes import Request


@dataclass(slots=True)
class Outcome:
    """Result of a single flow step.

    Carries:
      * control   – what happens next (Stop / Continue / …)
      * effects   – side effects the engine must apply
      * pipeline  – items to prepend to the flow's pipeline list
      * value     – optional result value
    """

    control: Control | None = None
    effects: Sequence[Effect] | None = field(default_factory=list)
    next_steps: list[str | Request] | None = None
    value: Any = None
