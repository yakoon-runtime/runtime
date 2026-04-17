from __future__ import annotations

from collections.abc import Callable

from kivy.factory import Factory
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView


class TabBar(BoxLayout):
    """
    UI-only: renders tab pills and emits on_select(tab_id).
    """

    def __init__(self, **kw):
        super().__init__(**kw)
        self._on_select: Callable[[str], None] | None = None

    def set_tabs(
        self, tabs: list[dict], active_id: str | None, on_select: Callable[[str], None]
    ):
        self._on_select = on_select
        self.clear_widgets()

        for t in tabs:
            btn = Factory.TabPill()
            btn.tab_id = t["id"]
            btn.text = t["title"]
            btn.active = t["id"] == active_id
            btn.bind(
                on_release=lambda _btn, tid=t["id"]: self._on_select
                and self._on_select(tid)
            )
            self.add_widget(btn)


class TabBarScroll(ScrollView):
    """
    UI-only: horizontal scroll + mousewheel mapping.
    """

    wheel_step = NumericProperty(0.08)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.button == "scrollup":
                self.scroll_x = min(1.0, self.scroll_x + self.wheel_step)
                return True
            if touch.button == "scrolldown":
                self.scroll_x = max(0.0, self.scroll_x - self.wheel_step)
                return True
        return super().on_touch_down(touch)
