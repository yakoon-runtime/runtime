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
        self._by_id = {}

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
        msg = getattr(view, "message", None)
        if msg is None:
            return

        vid = getattr(view, "id", None)
        mode = getattr(view, "mode", None)

        text = self._render_message_only(view)  # gleich unten

        if vid and mode == "replace" and vid in self._by_id:
            idx = self._by_id[vid]
            self._data[idx]["text"] = text
            self.ids.rv.data = list(self._data)
            self.ids.rv.refresh_from_data()
            self._scroll_trigger()
            return

        # neu anlegen
        self._data.insert(0, {"text": text})
        # indices verschieben
        for k in list(self._by_id.keys()):
            self._by_id[k] += 1
        if vid:
            self._by_id[vid] = 0

        self.ids.rv.data = self._data
        self._scroll_trigger()

    def _render_message_only(self, view) -> str:
        msg = getattr(view, "message", None)
        if msg is None:
            return ""

        blocks = getattr(msg, "blocks", []) or []
        parts = []
        for b in blocks:
            if getattr(b, "type", None) == "text":
                parts.append(str(getattr(b, "text", "")))
        return "\n".join([p for p in parts if p]).rstrip()

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

    def set_assist(self, text: str, state: str = "question") -> None:
        def _apply(_dt):
            self.ids.prompt.assist_text = text or ""
            self.ids.prompt.assist_state = state if text else "idle"

        Clock.schedule_once(_apply, 0)

    def clear_assist(self) -> None:
        def _apply(_dt):
            self.ids.prompt.assist_text = ""
            self.ids.prompt.assist_state = "idle"

        Clock.schedule_once(_apply, 0)


Factory.register("ChatWidget", cls=ChatWidget)
