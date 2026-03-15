from .base import BaseRenderer
from .kv import KVRenderer
from .kv_item import KVItemRenderer
from .list import ListRenderer
from .rule import RuleRenderer
from .spacer import SpacerRenderer
from .text import TextRenderer


class RendererBuilder:

    def __init__(self, surface):
        self._surface = surface
        self._types = {
            "text": TextRenderer,
            "rule": RuleRenderer,
            "spacer": SpacerRenderer,
            "list": ListRenderer,
            "kv": KVRenderer,
            "kv_item": KVItemRenderer,
        }

    def create(self, node) -> BaseRenderer:
        cls = self._types.get(node.type)
        if not cls:
            raise RuntimeError(f"No renderer for {node.type}.")

        return cls(node, self._surface)
