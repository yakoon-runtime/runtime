from __future__ import annotations

from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.label import Label


class TextBlockWidget(Label):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.halign = "left"
        self.valign = "top"
        self.text_size = (self.width, None)
        self.size_hint_y = None
        self.bind(width=self._reflow, text=self._reflow)

    def _reflow(self, *_):
        self.text_size = (self.width, None)
        self.texture_update()
        self.height = self.texture_size[1] + dp(6)


Factory.register("TextBlockWidget", cls=TextBlockWidget)
