from __future__ import annotations

from yakoon.kivy.widgets.blocks.block import BlockRenderer
from yakoon.kivy.widgets.blocks.block_header import HeaderBlockRenderer
from yakoon.kivy.widgets.blocks.block_kv import KvBlockRenderer, KvItemBlockRenderer
from yakoon.kivy.widgets.blocks.block_list import (
    ListBlockRenderer,
    ListItemBlockRenderer,
)
from yakoon.kivy.widgets.blocks.block_ruler import RulerBlockRenderer
from yakoon.kivy.widgets.blocks.block_spacer import SpacerBlockRenderer
from yakoon.kivy.widgets.blocks.block_text import TextBlockRenderer


class BlockRendererRegistry:

    def __init__(self, dbg=False):
        self._dbg = dbg
        self._by_type: dict[str, BlockRenderer] = {
            "text": TextBlockRenderer(),
            "header": HeaderBlockRenderer(),
            "spacer": SpacerBlockRenderer(),
            "rule": RulerBlockRenderer(),
            "list": ListBlockRenderer(self),
            "list_item": ListItemBlockRenderer(self),
            "kv": KvBlockRenderer(self),
            "kv_item": KvItemBlockRenderer(self),
        }

    def render(self, node):
        return self._by_type[node.type].render(node)
