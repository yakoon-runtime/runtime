from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.widget import Widget

RulerStyle = Literal["subtle", "normal", "strong"]


class RulerBlockLike(Protocol):
    style: RulerStyle


class RulerBlockWidget(Widget):
    """
    UI behavior only:
    - draws a horizontal line using canvas.after
    - all parameters are properties (set by renderer / kv)
    """

    # from theme.kv (RGB); alpha is derived from style
    rgba = ListProperty([1, 1, 1, 1])

    # public inputs
    style = StringProperty("normal")  # subtle|normal|strong
    inset_dp = NumericProperty(4.0)  # left/right inset in dp

    # derived drawing params (dp already applied where appropriate)
    _alpha = NumericProperty(0.25)
    _thickness = NumericProperty(1.5)  # dp value (already dp())
    _pad_y = NumericProperty(2.0)  # dp value (already dp())

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            style=self._apply_style,
            inset_dp=self._redraw,
            rgba=self._redraw,
        )
        self._apply_style()

    def _apply_style(self, *_: object) -> None:
        s = self.style
        if s == "subtle":
            self._alpha = 0.12
            self._thickness = float(dp(1))
            self._pad_y = float(dp(2))
        elif s == "strong":
            self._alpha = 0.50
            self._thickness = float(dp(1.5))
            self._pad_y = float(dp(2))
        else:  # normal
            self._alpha = 0.25
            self._thickness = float(dp(1.5))
            self._pad_y = float(dp(2))

        # Height is a function of thickness/padding; keep it deterministic.
        # If you want extra whitespace, increase via pad_y or a separate "height_dp".
        self.height = self._thickness + self._pad_y * 2

        self._redraw()

    def _redraw(self, *_: object) -> None:
        self.canvas.after.clear()
        with self.canvas.after:
            r, g, b, _ = self.rgba
            Color(r, g, b, self._alpha)

            inset = dp(self.inset_dp)
            y = self.y + self._pad_y + self._thickness / 2
            x1 = self.x + inset
            x2 = self.right - inset

            Line(points=[x1, y, x2, y], width=self._thickness)


@dataclass(slots=True)
class RulerBlockRenderer:

    def render(self, node) -> Widget:

        style = node.props.get("style", "normal")
        w = RulerBlockWidget()
        w.style = style

        return w
