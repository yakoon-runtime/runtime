from __future__ import annotations

from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.widget import Widget


class SpacerBlockWidget(Widget):
    def __init__(self, height_dp: float = 12, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.height = dp(height_dp)


Factory.register("SpacerBlockWidget", cls=SpacerBlockWidget)
