from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .control import Control
from .effect import Effect


class Outcome:
    """Result of a single flow step.

    Carries an optional control (what happens next) and a list of
    effects (side effects the engine must apply).
    """

    def __init__(
        self,
        control: Control | None = None,
        effects: Sequence[Effect] | None = None,
        value: Any = None,
    ) -> None:
        self.control = control
        self.effects = effects or []
        self.value = value
