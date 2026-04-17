from __future__ import annotations

from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout


class TabViewPage(BoxLayout):
    """
    Container für den aktiven Tab-Content.
    Der Controller setzt hier das aktuell aktive Page-Widget hinein.
    """

    current = ObjectProperty(allownone=True)

    def set_content(self, widget):
        host = self.ids.get("content_host")
        if not host:
            return

        if self.current is widget:
            return

        host.clear_widgets()
        if widget is not None:
            host.add_widget(widget)
        self.current = widget

    def focus_active(self):
        w = self.current
        if w and hasattr(w, "focus_prompt"):
            w.focus_prompt()


Factory.register("TabViewPage", cls=TabViewPage)
