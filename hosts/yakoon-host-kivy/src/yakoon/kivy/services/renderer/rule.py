from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kivy.uix.widget import Widget
from yakoon.kivy.widgets.blocks.ruler import RulerBlockWidget


@dataclass(slots=True)
class RulerBlockRenderer:
    def render(self, block: Any) -> Widget:
        return RulerBlockWidget(style=getattr(block, "style", "normal"))
