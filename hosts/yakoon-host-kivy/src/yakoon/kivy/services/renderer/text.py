from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kivy.uix.widget import Widget
from yakoon.kivy.widgets.blocks.text import TextBlockWidget


@dataclass(slots=True)
class TextBlockRenderer:

    def render(self, block: Any) -> Widget:
        w = TextBlockWidget()
        w.text = str(getattr(block, "text", "") or "")
        return w
