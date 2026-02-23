from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout


class PromptWidget(BoxLayout):

    # hint = StringProperty("shell$ ")
    prefix = StringProperty("shell$")  # wird später von Session gesetzt
    secret = BooleanProperty(False)
    multiline = BooleanProperty(True)

    assist_text = StringProperty("")
    assist_state = OptionProperty("idle", options=("idle", "question", "error"))

    min_h = NumericProperty(dp(44))  # 1 Zeile
    max_h = NumericProperty(dp(160))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_submit")

    def on_kv_post(self, base_widget):
        Window.bind(on_key_down=self._on_window_key_down)

    @property
    def input(self):
        return self.ids.input

    def focus_input(self):
        Clock.schedule_once(lambda _dt: setattr(self.input, "focus", True), 0)

    def _submit_internal(self):
        text = (self.input.text or "").strip()
        self.input.text = ""
        if not text:
            self.focus_input()
            return
        self.dispatch("on_submit", text)
        self.focus_input()

    def on_submit(self, text: str):
        """Event stub: will be bound from KV or parent widget."""
        pass

    def _on_window_key_down(self, _window, key, scancode, codepoint, modifiers):
        ti = self.input

        # Nur reagieren, wenn der Prompt fokussiert ist
        if not ti.focus:
            return False

        # Enter-Key in Kivy: key == 13 (meist) oder 271 (numpad enter)
        is_enter = key in (13, 271)
        if not is_enter:
            return False

        mods = set(modifiers or [])

        if "shift" in mods:
            # Shift+Enter = neue Zeile
            # (Kivy würde das eh tun, aber wir kontrollieren es explizit)
            ti.insert_text("\n")
            # optional: nach unten scrollen
            ti.scroll_y = 0
            return True

        # Enter = Submit
        self._submit_internal()
        return True


Factory.register("PromptWidget", cls=PromptWidget)
