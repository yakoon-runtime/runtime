from kivy.clock import Clock
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout


class ChatWidget(BoxLayout):

    def __init__(self, on_submit, **kw):

        super().__init__(**kw)
        self.on_submit = on_submit
        self._scroll_trigger = Clock.create_trigger(self._scroll_to_bottom, 0)

        self._data = []
        self.runner = None
        self.session = None

    @property
    def prompt(self):
        return self.ids.prompt

    def _is_near_bottom(self):
        return self.ids.rv.scroll_y <= 0.02

    def _scroll_to_bottom(self, _dt):
        rv = self.ids.rv

        # Wenn Inhalt kleiner als Viewport ist: nicht "scrollen" (verhindert Bounce)
        lm = rv.layout_manager
        if not lm:
            return
        if lm.height <= rv.height:
            return

        rv.scroll_y = 0

    def apply_context(self, ctx):

        # Output anzeigen
        if ctx.envelope.text:
            self.append_message(ctx.envelope.text)

        ui = ctx.ui_state_provider()
        self.ids.prompt.prefix = ui.prompt_prefix
        self.ids.prompt.secret = ui.prompt_secret

    def append_message(self, text: str):

        if not text.endswith("\n"):
            text += "\n"
        self._data.append({"text": text})
        self.ids.rv.data = self._data

        # kein schedule_once scroll_y=0 mehr
        self._scroll_trigger()

    def submit(self, text: str):

        # echo
        self.append_message(f"> **{self.ids.prompt.prefix}** '{text}'")
        # self.append_message(f"{text}")

        if self.on_submit:
            self.on_submit(text)

        # Fokus behalten
        Clock.schedule_once(lambda _dt: setattr(self.ids.prompt, "focus", True), 0)

    def focus_prompt(self):
        self.ids.prompt.focus_input()


Factory.register("ChatWidget", cls=ChatWidget)
