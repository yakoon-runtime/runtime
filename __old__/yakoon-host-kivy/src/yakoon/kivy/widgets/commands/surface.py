from __future__ import annotations

import uuid
from typing import Any

from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout

from .snapshot import MessageSnapshot


class CommandSurface(BoxLayout):
    busy = BooleanProperty(False)

    TOP_EPS = 0.98

    def __init__(self, on_submit, **kw):
        super().__init__(**kw)

        self.on_submit = on_submit
        self.runner = None
        self.session = None

        self._active_vid: str | None = None
        self._assist_error: str | None = None

        self._awaiting_result: bool = False

        self._rows: dict[str, dict[str, Any]] = {}
        self._idx_by_vid: dict[str, int] = {}

        self._dirty_rows: set[str] = set()
        self._render_trigger = Clock.create_trigger(self._flush_rows, 0)

        self._refresh_trigger = Clock.create_trigger(self._refresh_from_data, 0)
        self._scroll_trigger = Clock.create_trigger(self._apply_scroll, 0)

        self._stick_to_top = True
        self._force_scroll = False

    def on_kv_post(self, base_widget):
        self.messages.bind(scroll_y=self._on_scroll_y)

    @property
    def prompt(self):
        return self.ids.prompt

    @property
    def messages(self):
        return self.ids.messages

    # --------------------------------------------------------
    # Scroll Handling
    # --------------------------------------------------------

    def _refresh_from_data(self, *_):
        self.messages.refresh_from_data()

    def _on_scroll_y(self, _rv, value: float):
        if self._force_scroll:
            return
        self._stick_to_top = value >= self.TOP_EPS

    def _request_scroll_to_top(self, *, force=False):
        if force:
            self._force_scroll = True
        self._scroll_trigger()

    def _apply_scroll(self, *_):
        self.messages.scroll_y = 1.0
        self._stick_to_top = True
        self._force_scroll = False

    def _maybe_autoscroll(self):
        if self._stick_to_top or self._force_scroll:
            self._request_scroll_to_top(force=self._force_scroll)

    # --------------------------------------------------------
    # Busy State
    # --------------------------------------------------------

    def set_busy(self, busy: bool):
        self.busy = busy

        def _apply(_dt):
            prompt = self.ids.prompt

            if hasattr(prompt, "locked"):
                prompt.locked = busy
            else:
                prompt.disabled = busy

        Clock.schedule_once(_apply, 0)

    # --------------------------------------------------------
    # Row Management
    # --------------------------------------------------------

    def _new_row(self, *, vid: str, header: Any | None):

        return {
            "viewclass": "CommandMessage",
            "vid": vid,
            "header": header,
            "snapshot": MessageSnapshot(),
            "size_hint": (1, None),
            "size": (0, dp(24)),
        }

    def _ensure_row(self, vid: str, header):
        row = self._rows.get(vid)
        if row:
            return row

        row = self._new_row(
            vid=vid,
            header=header,
        )

        self.messages.data.insert(0, row)

        self._rows[vid] = row
        self._reindex()

        self._maybe_autoscroll()
        return row

    def _reindex(self):

        self._idx_by_vid.clear()

        for i, row in enumerate(self.messages.data):
            self._idx_by_vid[row["vid"]] = i

    # --------------------------------------------------------
    # Rendering
    # --------------------------------------------------------

    def apply_context(self, ctx):
        event = ctx.envelope
        ui = ctx.ui_state_provider()
        self.ids.prompt.prefix = ui.prompt_prefix
        self.ids.prompt.secret = ui.prompt_secret

        header = getattr(event, "header", None)
        if (
            header
            and getattr(header, "role", None) == "error"
            and getattr(header, "error_kind", None) == "validation"
        ):
            self._assist_error = self._extract_text_from_event(event)
            self.ids.prompt.assist_text = self._assist_error
            self.ids.prompt.assist_state = "error"

        self.render(event)

    def _extract_text_from_event(self, event: Any) -> str:
        texts: list[str] = []
        patch = getattr(event, "patch", None)
        for op in getattr(patch, "ops", None) or []:
            block = getattr(op, "block", None)
            text = getattr(block, "text", None)
            if isinstance(text, str) and text:
                texts.append(text)
        return "\n".join(texts)

    def render(self, event):
        patch = getattr(event, "patch", None)
        if patch is None:
            return

        if getattr(patch, "final", False):
            self._awaiting_result = False
            self.set_busy(False)

        self.apply_event(event)

    def apply_event(self, event):

        vid = getattr(event, "id", None) or uuid.uuid4().hex

        patch = getattr(event, "patch", None)
        if patch is None:
            return

        start_new = any(getattr(op, "op", None) == "reset" for op in (patch.ops or []))

        if start_new:
            self._active_vid = vid

        row = self._ensure_row(
            vid,
            getattr(event, "header", None),
        )

        row["snapshot"].apply_patch(patch)

        self._dirty_rows.add(vid)

        self._render_trigger()

    # --------------------------------------------------------
    # Input
    # --------------------------------------------------------

    def submit(self, text: str):
        if self.busy:
            return

        # print("SURFACE SUBMIT:", repr(text))
        self._request_scroll_to_top(force=True)
        self._awaiting_result = True
        self.set_busy(True)

        if self.on_submit:
            self.on_submit(text)

        Clock.schedule_once(lambda _dt: self.focus_prompt(), 0.01)

    def focus_prompt(self):
        self.ids.prompt.focus_input()

    def set_assist(self, text: str, state: str = "question") -> None:
        def _apply(_dt):
            self.set_busy(False)
            if self._assist_error and state == "question":
                return
            self.ids.prompt.assist_text = text or ""
            self.ids.prompt.assist_state = state if text else "idle"

        Clock.schedule_once(_apply, 0)

    def clear_assist(self) -> None:
        def _apply(_dt):
            if self._assist_error:
                return
            self.ids.prompt.assist_text = ""
            self.ids.prompt.assist_state = "idle"

        Clock.schedule_once(_apply, 0)

    def _flush_rows(self, *_):

        for vid in self._dirty_rows:

            idx = self._idx_by_vid.get(vid)
            if idx is None:
                continue

            row = self._rows[vid]

            # wichtig: neues dict erzeugen
            self.messages.data[idx] = dict(row)

        self._dirty_rows.clear()


Factory.register("CommandSurface", cls=CommandSurface)
