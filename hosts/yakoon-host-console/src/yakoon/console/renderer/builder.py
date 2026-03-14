from .base import BaseRenderer
from .header import HeaderRenderer
from .kv import KVRenderer
from .list import ListRenderer
from .rule import RuleRenderer
from .spacer import SpacerRenderer
from .text import TextRenderer


class RendererBuilder:

    def __init__(self, surface):
        self._surface = surface
        self._types = {
            "text": TextRenderer,
            "header": HeaderRenderer,
            "rule": RuleRenderer,
            "spacer": SpacerRenderer,
            "list": ListRenderer,
            "kv": KVRenderer,
        }

    def create(self, node) -> BaseRenderer:
        cls = self._types.get(node.type)
        if not cls:
            raise RuntimeError(f"No renderer for {node.type}.")

        return cls(node, self._surface)
