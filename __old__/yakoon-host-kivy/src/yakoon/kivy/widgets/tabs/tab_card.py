from kivy.clock import Clock
from kivy.factory import Factory
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout


class TabCard(ButtonBehavior, BoxLayout):

    tab_id = StringProperty("")
    title = StringProperty("")
    _suppress_open = BooleanProperty(False)

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.register_event_type("on_open")
        self.register_event_type("on_close")

    # --- events ----------------------------------------------------------

    def on_open(self, *args):
        pass

    def on_close(self, *args):
        pass

    # --- actions ---------------------------------------------------------

    def open(self):
        if self._suppress_open:
            return
        self.dispatch("on_open", self.tab_id)

    def close(self):
        # verhindert, dass der Card-Release danach noch open triggert
        self._suppress_open = True
        Clock.schedule_once(self._unsuppress, 0)
        self.dispatch("on_close", self.tab_id)

    def _unsuppress(self, _dt):
        self._suppress_open = False

    # --- ButtonBehavior hook --------------------------------------------

    def on_release(self):
        self.open()


Factory.register("TabCard", cls=TabCard)
