from __future__ import annotations

from typing import Any, Protocol

from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget


class BlockRenderer(Protocol):
    def render(self, block: Any) -> Widget: ...


class DebugBackgroundMixin:
    """
    Adds a colored background rectangle to a widget.
    Call `self._dbg_bg(r, g, b, a)` in __init__ after super().
    """

    def _dbg_bg(self, r=1, g=0, b=1, a=0.12):
        with self.canvas.before:
            self._dbg_color = Color(r, g, b, a)
            self._dbg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._dbg_update, size=self._dbg_update)

    def _dbg_update(self, *_):
        self._dbg_rect.pos = self.pos
        self._dbg_rect.size = self.size
