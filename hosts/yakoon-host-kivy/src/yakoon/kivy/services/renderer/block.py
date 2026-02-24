from __future__ import annotations

from typing import Any, Protocol

from kivy.uix.widget import Widget


class BlockRenderer(Protocol):
    def render(self, block: Any) -> Widget: ...
