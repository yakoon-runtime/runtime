from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from kivy.metrics import dp
from kivy.uix.widget import Widget


class SpacerBlockLike(Protocol):
    size: float


class SpacerBlockWidget(Widget):
    pass


@dataclass(slots=True)
class SpacerBlockRenderer:

    default_height_dp: float = 12.0

    def render(self, block: SpacerBlockLike) -> Widget:
        w = SpacerBlockWidget()
        w.height = dp(block.size)
        return w
