from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kivy.factory import Factory
from kivy.metrics import dp, sp
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from yakoon.kivy.themes.active import active_theme


class TextBlockWidget(Label):

    DEFAULT_FONT_SIZE = sp(16)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.font_size = self.DEFAULT_FONT_SIZE
        self.halign = "left"
        self.valign = "top"
        self.text_size = (self.width, None)
        self.size_hint_y = None
        self.color = active_theme.text
        self.bind(width=self._reflow, text=self._reflow)

    def _reflow(self, *_):
        self.text_size = (self.width, None)
        self.texture_update()
        self.height = self.texture_size[1] + dp(6)


@dataclass(slots=True)
class TextBlockRenderer:

    def render(self, block: Any) -> Widget:
        w = TextBlockWidget()
        w.text = str(getattr(block, "text", "") or "")
        return w


Factory.register("TextBlockWidget", cls=TextBlockWidget)
