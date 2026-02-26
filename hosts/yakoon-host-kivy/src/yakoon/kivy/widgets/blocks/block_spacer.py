from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.widget import Widget


class SpacerBlockWidget(Widget):

    def __init__(self, height_dp: float = 12, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.height = dp(height_dp)


@dataclass(slots=True)
class SpacerBlockRenderer:
    default_height_dp: float = 12

    def render(self, block: Any) -> Widget:
        h = getattr(block, "size", None)
        try:
            height_dp = float(h) if h is not None else self.default_height_dp
        except Exception:
            height_dp = self.default_height_dp
        return SpacerBlockWidget(height_dp=height_dp)


Factory.register("SpacerBlockWidget", cls=SpacerBlockWidget)
