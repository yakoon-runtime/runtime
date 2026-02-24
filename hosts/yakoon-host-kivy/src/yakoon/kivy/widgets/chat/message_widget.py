from __future__ import annotations

from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from yakoon.kivy.services.registry import BlockRendererRegistry


class ChatMessageWidget(BoxLayout):

    def __init__(self, registry: BlockRendererRegistry | None = None, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"

        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))

        self.spacing = 0
        self.registry = registry or BlockRendererRegistry()

    def set_message(self, message) -> None:
        self.clear_widgets()
        blocks = getattr(message, "blocks", None) or []
        for b in blocks:
            self.add_widget(self.registry.render(b))
        self.height = self.minimum_height


Factory.register("ChatMessageWidget", cls=ChatMessageWidget)
