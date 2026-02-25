from __future__ import annotations

from yakoon.kivy.services.renderer.block import BlockRenderer
from yakoon.kivy.services.renderer.rule import RulerBlockRenderer
from yakoon.kivy.services.renderer.spacer import SpacerBlockRenderer
from yakoon.kivy.services.renderer.text import TextBlockRenderer


class BlockRendererRegistry:

    def __init__(self, dbg=False):
        self._dbg = dbg
        self._by_type: dict[str, BlockRenderer] = {
            "text": TextBlockRenderer(),
            "spacer": SpacerBlockRenderer(),
            "rule": RulerBlockRenderer(),
        }

    def render(self, block):
        content = self._by_type[block.type].render(block)
        return content
