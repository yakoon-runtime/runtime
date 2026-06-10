from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from .control import Control
from .effect import Effect


@dataclass(slots=True)
class Outcome:
    """Result of a single flow step.

    Carries an optional control (what happens next) and a list of
    effects (side effects the engine must apply).
    """

    control: Control | None = None
    effects: Sequence[Effect] | None = field(default_factory=list)
    value: Any = None
