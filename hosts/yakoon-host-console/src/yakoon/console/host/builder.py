# builder.py

from .renderer.kv import KVRenderer
from .renderer.list import ListRenderer
from .renderer.rule import RuleRenderer
from .renderer.spacer import SpacerRenderer
from .renderer.text import TextRenderer


class RendererBuilder:

    def __init__(self):
        self._types = {
            "text": TextRenderer,
            "rule": RuleRenderer,
            "spacer": SpacerRenderer,
            "list": ListRenderer,
            "kv": KVRenderer,
        }

    def create(self, node):
        cls = self._types.get(node.type)
        if not cls:
            return None
        return cls(node)
