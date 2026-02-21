from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.recycleview.views import RecycleDataViewBehavior


class ChatRow(RecycleDataViewBehavior, Label):

    min_h = dp(18)  # Minimum
    pad_y = dp(2)

    def refresh_view_attrs(self, rv, index, data):
        super().refresh_view_attrs(rv, index, data)
        self.text = data.get("text", "")
        self.text_size = (self.width, None)
        self.halign = "left"
        self.valign = "top"

        self.texture_update()
        content_h = self.texture_size[1] + self.pad_y
        self.height = max(self.min_h, content_h)
        return True

    def on_size(self, *_):
        self.text_size = (self.width, None)
        self.texture_update()
        content_h = self.texture_size[1] + self.pad_y
        self.height = max(self.min_h, content_h)


Factory.register("ChatRow", cls=ChatRow)
