from kivy.clock import Clock
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from yakoon.kivy.models.mount import RenderMount
from yakoon.kivy.services.render import ChatRenderService


class ChatWidget(BoxLayout):

    def __init__(self, on_submit, **kw):

        super().__init__(**kw)
        self.on_submit = on_submit
        self._scroll_trigger = Clock.create_trigger(self._restore_scroll_if_needed, 0)

        self._data = []
        self.runner = None
        self.session = None

        self._render = ChatRenderService()
        self._history = []
        self._by_id = {}
        self._live_vid: str | None = None

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
        mounts = self._render.render(view)
        for m in mounts:
            if m.target == "live":
                self._apply_live(m)
            else:
                self._apply_history(m)
        self._scroll_trigger()

    def _apply_live(self, m: RenderMount) -> None:
        if m.op == "set_live":
            self._live_vid = m.vid
            self.ids.live.set_view(m.payload)
        elif m.op == "clear_live":
            if self._live_vid == m.vid:
                self._live_vid = None
                self.ids.live.clear()

    def _apply_history(self, m: RenderMount) -> None:
        if m.op == "append_history":
            self._history.insert(0, m.payload)
            # shift indices
            for k in list(self._by_id.keys()):
                self._by_id[k] += 1
            if m.vid:
                self._by_id[m.vid] = 0
            self.ids.rv.data = list(self._history)
            self.ids.rv.refresh_from_data()

    def submit(self, text: str):

        # echo
        # self.append_message(f"> **{self.ids.prompt.prefix}** '{text}'")
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
