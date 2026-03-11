# builder.py

from yakoon.console.host.renderer.base import BaseRenderer
from yakoon.console.host.renderer.header import HeaderRenderer

from .renderer.kv import KVRenderer
from .renderer.list import ListRenderer
from .renderer.rule import RuleRenderer
from .renderer.spacer import SpacerRenderer
from .renderer.text import TextRenderer


class RendererBuilder:

    def __init__(self):
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

        return cls(node)
