from kivy.clock import Clock
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from yakoon.kivy.widgets.commands.message import CommandMessage


class CommandSurface(BoxLayout):

    def __init__(self, on_submit, **kw):

        super().__init__(**kw)
        self.on_submit = on_submit
        self._scroll_trigger = Clock.create_trigger(self._restore_scroll_if_needed, 0)

        self.runner = None
        self.session = None

        self._active: CommandMessage | None = None
        self._prev: CommandMessage | None = None
        self._active_vid: str | None = None

    @property
    def prompt(self):
        return self.ids.prompt

    def _restore_scroll_if_needed(self, *_):
        self.ids.scroll.scroll_y = 1.0

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
        vid = getattr(view, "id", None)
        mode = getattr(view, "mode", None)

        # ensure we have an active container for this stream/view
        if self._active is None or (
            vid and self._active_vid != vid and mode in ("patch", "replace")
        ):
            # rotate old active to prev
            if self._active is not None:
                if self._prev is not None:
                    try:
                        self._prev.dispose()
                    except Exception:
                        pass
                self._prev = self._active

            self._active = CommandMessage()
            self._active_vid = vid

            # rebuild stack (max 2)
            stack = self.ids.stack
            stack.clear_widgets()
            stack.add_widget(self._active)
            if self._prev is not None:
                stack.add_widget(self._prev)

        # ---- PATCH STREAMING ----
        if mode == "patch":
            patch = getattr(view, "patch", None)
            if patch is not None:
                self._active.apply_patch(patch)
            self._scroll_trigger()
            return

        # ---- NORMAL FULL VIEW ----
        # in-place update for replace on same vid
        if mode == "replace" and vid and self._active_vid == vid:
            self._active.set_view(view)
            self._scroll_trigger()
            return

        # fallback: treat as new full view (no vid or different semantics)
        self._active.set_view(view)
        self._scroll_trigger()

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


Factory.register("CommandSurface", cls=CommandSurface)
