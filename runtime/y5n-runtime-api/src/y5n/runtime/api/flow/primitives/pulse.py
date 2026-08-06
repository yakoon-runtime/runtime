from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .control import Control
from .effect import Effect

if TYPE_CHECKING:
    from y5n.runtime.api.nodes import Invocation


@dataclass(frozen=True, slots=True)
class Pulse:
    """What a flow hands to the runtime at each yield point.

    A flow executes until it emits its next pulse. The runtime applies the
    pulse's effects and decides, via control, what happens next.

    Carries:
      * control   - the lifecycle instruction (Stop / Continue / …)
      * effects   - side effects the runtime must apply
      * pipeline  - items to prepend to the flow's pipeline list
    """

    control: Control | None = None
    effects: Sequence[Effect] | None = field(default_factory=list)
    next_steps: list[str | Invocation] | None = None
