from __future__ import annotations

from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from yakoon.kivy.services.registry import BlockRendererRegistry

from .message_widget import ChatMessageWidget


class ChatLiveArea(BoxLayout):
    """
    Shows exactly one 'live' (streaming) message.
    The orchestrator (ChatWidget/ChatRenderService) decides when to set/clear it.
    """

    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))

        self.spacing = 0

        self._view = None
        self._registry = BlockRendererRegistry()
        self._msg = ChatMessageWidget(registry=self._registry)

        self.add_widget(self._msg)

    def set_view(self, view) -> None:
        """Mount or update the live view."""
        self._view = view
        msg = getattr(view, "message", None) if view else None
        if msg is None:
            self.clear()
            return
        self._msg.set_message(msg)
        self.opacity = 1
        self.disabled = False

    def clear(self) -> None:
        """Remove the live view."""
        self._view = None
        self._msg.clear_widgets()
        # hide live area
        self.opacity = 0
        self.disabled = True
        self.height = 0


Factory.register("ChatLiveArea", cls=ChatLiveArea)
