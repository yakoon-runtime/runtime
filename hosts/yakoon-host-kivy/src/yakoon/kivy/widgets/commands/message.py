# container.py
from __future__ import annotations

from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from yakoon.kivy.services.registry import BlockRendererRegistry


class CommandMessage(BoxLayout):
    """
    Container for one rendered ViewSpec.message.
    Later responsibilities:
      - echo header
      - toolbar (copy etc.)
      - dispose animation (pixel dissolve)
    """

    def __init__(self, registry: BlockRendererRegistry | None = None, **kw):
        super().__init__(**kw)

        self.orientation = "vertical"
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))

        self._registry = registry or BlockRendererRegistry(dbg=True)
        self._view = None
        # self._dbg_bg(0, 0.6, 1, 0.10)

    @property
    def view(self):
        return self._view

    def set_view(self, view) -> None:
        self._view = view
        self.clear_widgets()

        msg = getattr(view, "message", None) if view else None
        blocks = getattr(msg, "blocks", None) if msg else None
        if not blocks:
            return

        # render blocks -> widgets
        for b in blocks:
            w = self._registry.render(b)
            # defensive: ensure vertical stacking participates in height
            try:
                if (
                    getattr(w, "size_hint_y", None) is None
                    and getattr(w, "height", None) is None
                ):
                    w.size_hint_y = None
            except Exception:
                pass
            self.add_widget(w)

    def dispose(self) -> None:
        # placeholder: animate then remove
        # e.g. animate opacity / dissolve -> then parent.remove_widget(self)
        pass


Factory.register("CommandMessage", cls=CommandMessage)
