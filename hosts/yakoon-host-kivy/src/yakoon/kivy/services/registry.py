from __future__ import annotations

from yakoon.kivy.services.renderer.block import BlockRenderer
from yakoon.kivy.services.renderer.rule import RulerBlockRenderer
from yakoon.kivy.services.renderer.spacer import SpacerBlockRenderer
from yakoon.kivy.services.renderer.text import TextBlockRenderer
from yakoon.kivy.widgets.blocks.base import BlockFrame


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

        # Spacer braucht evtl. keinen Frame – aber ich würde ihn trotzdem wrappen,
        # dann ist spacing konsistent (oder pad_y=0).
        if block.type == "spacer":
            frame = BlockFrame(pad_y=0, dbg=self._dbg)
        elif block.type == "ruler":
            frame = BlockFrame(pad_y=6, dbg=self._dbg)
        else:
            frame = BlockFrame(pad_y=6, dbg=self._dbg)

        frame.set_content(content)
        return frame
