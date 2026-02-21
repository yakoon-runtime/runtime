from kivy.app import App
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout


class AppRootPage(BoxLayout):

    sidebar_width = NumericProperty(0)

    # optional: nützlich zum Debuggen / KV-Binding
    current_screen = StringProperty("tabs")

    def __init__(self, **kw):
        super().__init__(**kw)
        self.controller = None  # wird von app.py gesetzt

    def set_controller(self, controller):
        self.controller = controller

    # --- Application Terminate ---------------------------------------------

    def stop_app(self):
        App.get_running_app().stop()

    # --- Screen switching -------------------------------------------------

    def show_screen(self, name: str):
        sm = self.ids.get("sm")
        if not sm:
            return
        if sm.current != name:
            sm.current = name
        self.current_screen = name

    # --- Topbar actions ---------------------------------------------------

    def on_right_action_1(self):
        if self.controller:
            self.controller.toggle_overview()

    def on_right_action_2(self):
        App.get_running_app().stop()

    # --- Sidebar ----------------------------------------------------------

    def toggle_sidebar(self):
        self.sidebar_width = dp(220) if self.sidebar_width == 0 else 0

    # --- Tabs UI ----------------------------------------------------------

    def on_new_tab(self):
        if self.controller:
            self.controller.new_chat_tab(select=True)


Factory.register("AppRootPage", cls=AppRootPage)
