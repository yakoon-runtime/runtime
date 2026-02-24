from __future__ import annotations

from kivy.factory import Factory
from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.widget import Widget


class RulerBlockWidget(Widget):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.height = dp(10)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self.canvas.after.clear()
        with self.canvas.after:
            Color(1, 1, 1, 0.18)
            y = self.y + self.height / 2
            Line(points=[self.x + dp(8), y, self.right - dp(8), y], width=1)


Factory.register("RulerBlockWidget", cls=RulerBlockWidget)
