from __future__ import annotations

from typing import Any

from kivy.uix.widget import Widget
from yakoon.kivy.services.renderer.block import BlockRenderer
from yakoon.kivy.services.renderer.rule import RulerBlockRenderer
from yakoon.kivy.services.renderer.spacer import SpacerBlockRenderer
from yakoon.kivy.services.renderer.text import TextBlockRenderer
from yakoon.kivy.widgets.blocks.text import TextBlockWidget


class BlockRendererRegistry:

    def __init__(self) -> None:
        self._by_type: dict[str, BlockRenderer] = {
            "text": TextBlockRenderer(),
            "spacer": SpacerBlockRenderer(),
            "ruler": RulerBlockRenderer(),
        }

    def render(self, block: Any) -> Widget:

        btype = str(getattr(block, "type", "") or "")
        r = self._by_type.get(btype)
        if r is None:
            # fallback: sichtbar machen, statt still zu droppen
            w = TextBlockWidget()
            w.text = str(block)
            return w
        return r.render(block)
