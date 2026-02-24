from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kivy.uix.widget import Widget
from yakoon.kivy.widgets.blocks.spacer import SpacerBlockWidget


@dataclass(slots=True)
class SpacerBlockRenderer:
    default_height_dp: float = 12

    def render(self, block: Any) -> Widget:
        h = getattr(block, "height", None)
        try:
            height_dp = float(h) if h is not None else self.default_height_dp
        except Exception:
            height_dp = self.default_height_dp
        return SpacerBlockWidget(height_dp=height_dp)
