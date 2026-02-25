from __future__ import annotations

from kivy.clock import Clock
from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.widget import Widget


class RulerBlockWidget(Widget):

    def __init__(self, style="normal", inset_dp=0, **kw):
        super().__init__(**kw)

        self.size_hint_x = 1
        self.size_hint_y = None

        self._style = style
        self._inset = dp(inset_dp)

        # style mapping
        if style == "subtle":
            self._alpha = 0.12
            self._thickness = dp(1)
            self._pad_y = 0
        elif style == "strong":
            self._alpha = 0.5
            self._thickness = dp(2)
            self._pad_y = 0
        else:  # normal
            self._alpha = 0.25
            self._thickness = dp(1.5)
            self._pad_y = 0

        # self.height = self._pad_y * dp(2) + self._thickness * 20
        self.height = self._thickness

        self.bind(pos=self._redraw, size=self._redraw)
        Clock.schedule_once(self._redraw, 0)

    def _redraw(self, *_):
        self.canvas.after.clear()
        with self.canvas.after:
            Color(1, 1, 1, self._alpha)

            y = self.y + self._pad_y + self._thickness / 2
            x1 = self.x + self._inset
            x2 = self.right - self._inset

            Line(points=[x1, y, x2, y], width=self._thickness)
