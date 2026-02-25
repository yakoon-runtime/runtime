from __future__ import annotations

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout


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


class BlockFrame(DebugBackgroundMixin, BoxLayout):

    def __init__(self, *, pad_y=6, pad_x=0, dbg=False, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.size_hint_x = 1
        self.size_hint_y = None
        self.padding = (dp(pad_x), dp(pad_y), dp(pad_x), dp(pad_y))
        self.bind(minimum_height=self.setter("height"))

        if dbg:
            self._dbg_bg(0.4, 0.8, 1, 0.08)  # hellblau

    def set_content(self, w):
        self.clear_widgets()
        self.add_widget(w)
