from kivy.clock import Clock
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout


class ChatWidget(BoxLayout):

    def __init__(self, on_submit, **kw):

        super().__init__(**kw)
        self.on_submit = on_submit
        self._scroll_trigger = Clock.create_trigger(self._restore_scroll_if_needed, 0)

        self._data = []
        self.runner = None
        self.session = None

    @property
    def prompt(self):
        return self.ids.prompt

    def _restore_scroll_if_needed(self, *_):
        self.ids.rv.scroll_y = 1.0

    def apply_context(self, ctx):

        view = ctx.envelope

        msg = getattr(view, "message", None)
        input_def = getattr(view, "input", None)

        ui = ctx.ui_state_provider()
        self.ids.prompt.prefix = ui.prompt_prefix
        self.ids.prompt.secret = ui.prompt_secret

        # --- Assist Logic ---
        prompt = self.ids.prompt

        # Wenn Fehler, zeige Fehlermeldung
        if msg and getattr(msg, "role", None) == "error":
            prompt.assist_text = self._extract_text(msg)
            prompt.assist_state = "error"
            return

        # Frage anzeigen
        if input_def:
            fields = input_def.fields or {}
            if fields:
                first_key = next(iter(fields.keys()))
                first = fields[first_key]
                label = getattr(first, "title", None) or first_key
            else:
                label = getattr(input_def, "title", None) or ""
            prompt.assist_text = label
            prompt.assist_state = "question"
            return

        prompt.assist_text = ""
        prompt.assist_state = "idle"
        self.render(view)

    def _extract_text(self, message):
        blocks = getattr(message, "blocks", []) or []
        texts = []
        for b in blocks:
            t = getattr(b, "text", None)
            if t:
                texts.append(str(t))
        return "\n".join(texts)

    def render(self, view) -> None:
        if hasattr(view, "message") and view.message is not None:
            self.append_message(str(view))

    def append_message(self, text: str):

        if not text.endswith("\n"):
            text += "\n"
        self._data.insert(0, {"text": text})
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
