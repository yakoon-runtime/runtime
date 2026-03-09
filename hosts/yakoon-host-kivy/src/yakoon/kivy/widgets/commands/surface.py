from __future__ import annotations

import uuid
from typing import Any

from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout


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

        self._doc_role: str | None = None
        self._doc_title: str | None = None
        self._doc_subtitle: str | None = None

        self._row_by_vid: dict[str, dict[str, Any]] = {}
        self._idx_by_vid: dict[str, int] = {}

        self._refresh_trigger = Clock.create_trigger(self._refresh_from_data, 0)
        self._scroll_trigger = Clock.create_trigger(self._apply_scroll, 0)

        self._stick_to_top: bool = True
        self._force_scroll: bool = False

    def on_kv_post(self, base_widget):
        self.messages.bind(scroll_y=self._on_scroll_y)

    @property
    def prompt(self):
        return self.ids.prompt

    @property
    def messages(self):
        return self.ids.messages

    def _refresh_from_data(self, *_):
        self.messages.refresh_from_data()

    def _on_scroll_y(self, _rv, value: float):
        if self._force_scroll:
            return
        self._stick_to_top = value >= self.TOP_EPS

    def _request_scroll_to_top(self, *, force: bool = False) -> None:
        if force:
            self._force_scroll = True
        self._scroll_trigger()

    def _apply_scroll(self, *_):
        self.messages.scroll_y = 1.0
        self._stick_to_top = True
        self._force_scroll = False

    def _maybe_autoscroll(self) -> None:
        if self._stick_to_top or self._force_scroll:
            self._request_scroll_to_top(force=self._force_scroll)

    def set_busy(self, busy: bool) -> None:
        self.busy = busy

        def _apply(_dt):
            prompt = self.ids.prompt
            if hasattr(prompt, "locked"):
                prompt.locked = busy
            else:
                prompt.disabled = busy

        Clock.schedule_once(_apply, 0)

    def _new_row(self, *, vid: str, first_event: Any | None) -> dict[str, Any]:
        return {
            "viewclass": "CommandMessage",
            "vid": vid,
            "size_hint": (1, None),
            "size": (0, dp(24)),
            "events": [first_event] if first_event is not None else [],
        }

    def _row_index(self, vid: str) -> int | None:
        return self._idx_by_vid.get(vid)

    def _replace_row_at(self, idx: int, row: dict[str, Any]) -> dict[str, Any]:
        new_row = dict(row)
        self.messages.data[idx] = new_row
        self._row_by_vid[new_row["vid"]] = new_row
        return new_row

    def _shift_indices_on_insert_top(self) -> None:
        for key in list(self._idx_by_vid.keys()):
            self._idx_by_vid[key] += 1

    def _insert_row_top(self, row: dict[str, Any]) -> None:
        self._shift_indices_on_insert_top()
        self.messages.data.insert(0, row)
        vid = row["vid"]
        self._row_by_vid[vid] = row
        self._idx_by_vid[vid] = 0
        self._refresh_trigger()
        self._maybe_autoscroll()

    def _get_visible_view(self, idx: int):
        adapter = getattr(self.messages, "view_adapter", None)
        if adapter is None:
            return None
        return adapter.views.get(idx)

    def _append_event(self, *, vid: str, event: Any) -> None:
        row = self._row_by_vid.get(vid)
        if row is None:
            row = self._new_row(vid=vid, first_event=None)
            self._insert_row_top(row)

        events = list(row.get("events") or [])
        events.append(event)
        row["events"] = events

        idx = self._row_index(vid)
        if idx is None:
            self._refresh_trigger()
            return

        row = self._replace_row_at(idx, row)
        widget = self._get_visible_view(idx)
        if widget is not None:
            try:
                widget.refresh_view_attrs(self.messages, idx, row)
            except Exception:
                self._refresh_trigger()
        else:
            self._refresh_trigger()

        self._update_visible_row_height(vid)
        self._maybe_autoscroll()

    def _update_visible_row_height(self, vid: str | None) -> None:
        if not vid:
            return
        idx = self._row_index(vid)
        if idx is None:
            return
        widget = self._get_visible_view(idx)
        if widget is None:
            return
        h = int(widget.get_calc_height())
        new_size = (0, max(1, h))
        row = self._row_by_vid.get(vid)
        if row is None:
            return
        if row.get("size") != new_size:
            row["size"] = new_size
            self._replace_row_at(idx, row)
            self.messages.refresh_from_layout()

    def _extract_text_from_event(self, event: Any) -> str:
        texts: list[str] = []
        patch = getattr(event, "patch", None)
        for op in getattr(patch, "ops", None) or []:
            block = getattr(op, "block", None)
            text = getattr(block, "text", None)
            if isinstance(text, str) and text:
                texts.append(text)
        return "\n".join(texts)

    def _update_header(self, event: Any) -> None:
        header = getattr(event, "header", None)
        if header is None:
            return
        self._doc_role = getattr(header, "role", None)
        self._doc_title = getattr(header, "title", None)
        self._doc_subtitle = getattr(header, "subtitle", None)

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

    def _has_body_ops(self, event: Any) -> bool:
        patch = getattr(event, "patch", None)
        for op in getattr(patch, "ops", None) or []:
            if getattr(op, "op", None) != "reset":
                return True
        return False

    def render(self, event) -> None:
        self._update_header(event)
        patch = getattr(event, "patch", None)
        if patch is None:
            return

        if getattr(patch, "final", False):
            self._awaiting_result = False
            self.set_busy(False)

        self.apply_event(event)

    def apply_event(self, event) -> None:
        vid = getattr(event, "id", None) or uuid.uuid4().hex
        patch = getattr(event, "patch", None)
        if patch is None:
            return

        start_new = any(getattr(op, "op", None) == "reset" for op in (patch.ops or []))
        if start_new:
            self._active_vid = vid

        if start_new and not self._has_body_ops(event):
            return

        if not self._active_vid:
            self._active_vid = vid

        self._append_event(vid=vid, event=event)

    def submit(self, text: str):
        if self.busy:
            return

        print("SURFACE SUBMIT:", repr(text))
        self._request_scroll_to_top(force=True)
        self._assist_error = None
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


Factory.register("CommandSurface", cls=CommandSurface)
