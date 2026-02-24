from __future__ import annotations

from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from yakoon.kivy.services.registry import BlockRendererRegistry

from .message_widget import ChatMessageWidget


class ChatMessageRow(RecycleDataViewBehavior, BoxLayout):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))

        self._msg = ChatMessageWidget(registry=BlockRendererRegistry())
        self.add_widget(self._msg)

    def refresh_view_attrs(self, rv, index, data):
        super().refresh_view_attrs(rv, index, data)
        view = data.get("view")
        msg = getattr(view, "message", None) if view else None
        if msg is not None:
            self._msg.set_message(msg)
            self.height = self.minimum_height
        return True


Factory.register("ChatMessageRow", cls=ChatMessageRow)
