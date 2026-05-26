from __future__ import annotations

from typing import Any

from y5n.kivy.widgets.blocks.registry import BlockRendererRegistry

from kivy.clock import Clock
from kivy.factory import Factory

# from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior


class CommandMessage(RecycleDataViewBehavior, BoxLayout):

    def __init__(self, registry=None, **kw):
        super().__init__(**kw)

        self.size_hint_y = None
        self.registry = registry or BlockRendererRegistry()
        self.bind(children=self._trigger_layout)

        self._trigger_layout = Clock.create_trigger(self._recalc_height, 0)

        self._vid: str | None = None

    # --------------------------------------------------------
    # RecycleView hook
    # --------------------------------------------------------

    def refresh_view_attrs(self, rv, index: int, data: dict[str, Any]):

        self._vid = data.get("vid")

        snapshot = data.get("snapshot")

        # Widget wird recycelt → alles löschen
        self.clear_widgets()

        if snapshot is None:
            self.height = 1
            return super().refresh_view_attrs(rv, index, data)

        widgets: dict[str, Any] = {}

        # ----------------------------------------------------
        # Structure
        # ----------------------------------------------------

        for node in snapshot.nodes:

            widget = self.registry.render(node)

            widget.bind(height=self._trigger_layout)

            widgets[node.id] = widget
            self.add_widget(widget)

        # ----------------------------------------------------
        # Text
        # ----------------------------------------------------

        for block_id, keys in snapshot.text.items():

            widget = widgets.get(block_id)
            if widget is None:
                continue

            append = getattr(widget, "append_text", None)
            if append is None:
                continue

            for key, text in keys.items():
                append(key, text)

        # ----------------------------------------------------
        # Height
        # ----------------------------------------------------

        # self._recalc_height()
        self._trigger_layout()
        return super().refresh_view_attrs(rv, index, data)

    # --------------------------------------------------------
    # Height calculation
    # --------------------------------------------------------

    def _recalc_height(self, *_):

        h = 0
        for child in self.children:
            h += child.height

        self.height = max(1, h)


Factory.register("CommandMessage", cls=CommandMessage)
