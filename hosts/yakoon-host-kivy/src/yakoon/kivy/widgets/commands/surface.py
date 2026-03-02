from __future__ import annotations

import uuid
from typing import Any

from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout


class CommandSurface(BoxLayout):
    """Surface owns the RV data-model (messages.data), not the widgets.

    - Newest message is inserted at index 0 (top).
    - RV viewclass (CommandMessage) rebuilds itself from row["events"].
    - Performance:
        * O(1) vid -> index mapping (no list.index() per patch)
        * If a row view is visible, update it directly via refresh_view_attrs()
          instead of triggering a full refresh_from_data() each time.
    - Auto-scroll:
        * User may scroll freely while streaming.
        * If the user is currently at the top (or submit() is called), we keep/force
          the view at the top so the newest message stays visible.
    """

    TOP_EPS = 0.98  # consider "at top" when scroll_y >= this

    def __init__(self, on_submit, **kw):
        super().__init__(**kw)
        self.on_submit = on_submit

        self.runner = None
        self.session = None

        self._active_vid: str | None = None
        self._assist_error: str | None = None

        # vid -> row dict stored in messages.data
        self._row_by_vid: dict[str, dict[str, Any]] = {}
        # vid -> index in messages.data (newest at 0)
        self._idx_by_vid: dict[str, int] = {}

        # refresh and scroll triggers
        self._refresh_trigger = Clock.create_trigger(self._refresh_from_data, 0)
        self._scroll_trigger = Clock.create_trigger(self._apply_scroll, 0)

        # if True, we keep the viewport at the top while new content arrives
        self._stick_to_top: bool = True
        # if True, we force a scroll-to-top on next tick (used on submit)
        self._force_scroll: bool = False

    def on_kv_post(self, base_widget):
        # Track whether the user is currently at the top. If they scroll away,
        # we stop auto-scrolling until they return to the top or submit again.
        rv = self.messages
        rv.bind(scroll_y=self._on_scroll_y)

    @property
    def prompt(self):
        return self.ids.prompt

    @property
    def messages(self):
        return self.ids.messages

    # ---------- refresh + scroll ----------

    def _refresh_from_data(self, *_):
        self.messages.refresh_from_data()

    def _on_scroll_y(self, _rv, value: float):
        # User intent: when user scrolls away from top, stop auto-stick.
        if self._force_scroll:
            return
        self._stick_to_top = value >= self.TOP_EPS

    def _request_scroll_to_top(self, *, force: bool = False) -> None:
        if force:
            self._force_scroll = True
        self._scroll_trigger()

    def _apply_scroll(self, *_):
        rv = self.messages
        rv.scroll_y = 1.0  # top
        self._stick_to_top = True
        self._force_scroll = False

    def _maybe_autoscroll(self) -> None:
        if self._stick_to_top or self._force_scroll:
            self._request_scroll_to_top(force=self._force_scroll)

    # ---------- model helpers ----------

    def _new_row(self, *, vid: str, first_event: Any | None) -> dict[str, Any]:
        return {
            "viewclass": "CommandMessage",
            "vid": vid,
            "size_hint": (1, None),
            # realistic placeholder reduces relayout jumps
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
        if not self._idx_by_vid:
            return
        for k in list(self._idx_by_vid.keys()):
            self._idx_by_vid[k] += 1

    def _insert_row_top(self, row: dict[str, Any]) -> None:
        self._shift_indices_on_insert_top()
        self.messages.data.insert(0, row)

        vid = row["vid"]
        self._row_by_vid[vid] = row
        self._idx_by_vid[vid] = 0

        # New row => refresh dataset so RV can create a view
        self._refresh_trigger()
        self._maybe_autoscroll()

    def _start_new_message(self) -> None:
        self._active_vid = uuid.uuid4().hex
        self._insert_row_top(self._new_row(vid=self._active_vid, first_event=None))

    def _get_visible_view(self, idx: int):
        rv = self.messages
        adapter = getattr(rv, "view_adapter", None)
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

        # If mounted, update directly (cheap). Otherwise schedule RV refresh.
        w = self._get_visible_view(idx)
        if w is not None:
            try:
                w.refresh_view_attrs(self.messages, idx, row)
            except Exception:
                self._refresh_trigger()
        else:
            self._refresh_trigger()

        # Keep height accurate so content is fully visible.
        self._update_visible_row_height(vid)

        self._maybe_autoscroll()

    # ---------- height sync (measured from visible widget) ----------

    def _update_visible_row_height(self, vid: str | None) -> None:
        if not vid:
            return

        idx = self._row_index(vid)
        if idx is None:
            return

        w = self._get_visible_view(idx)
        if w is None:
            return

        h = int(w.get_calc_height())
        new_size = (0, max(1, h))

        row = self._row_by_vid.get(vid)
        if row is None:
            return

        if row.get("size") != new_size:
            row["size"] = new_size
            self._replace_row_at(idx, row)
            self.messages.refresh_from_layout()

    # ---------- context + rendering ----------

    def _extract_text(self, message):
        blocks = getattr(message, "blocks", []) or []
        texts: list[str] = []
        for b in blocks:
            t = getattr(b, "text", None)
            if t:
                texts.append(str(t))
        return "\n".join(texts)

    def apply_context(self, ctx):
        view = ctx.envelope
        msg = getattr(view, "message", None)

        ui = ctx.ui_state_provider()
        self.ids.prompt.prefix = ui.prompt_prefix
        self.ids.prompt.secret = ui.prompt_secret

        # Assist: only validation errors
        if (
            msg
            and getattr(msg, "role", None) == "error"
            and getattr(msg, "error_kind", None) == "validation"
        ):
            self._assist_error = self._extract_text(msg)
            self.ids.prompt.assist_text = self._assist_error
            self.ids.prompt.assist_state = "error"

        self.render(view)

    def render(self, view) -> None:
        mode = getattr(view, "mode", None)

        if mode == "patch":
            patch = getattr(view, "patch", None)
            if patch is not None:
                self.apply_patch(patch)
        else:
            self.apply_view(view)

    def apply_patch(self, patch) -> None:
        if patch is None:
            return

        start_new = any(
            getattr(op, "op", None) == "reset"
            for op in (getattr(patch, "ops", None) or [])
        )

        if start_new or not self._active_vid:
            self._start_new_message()

        self._append_event(vid=self._active_vid, event=patch)

    def apply_view(self, view) -> None:
        self._active_vid = uuid.uuid4().hex
        self._insert_row_top(self._new_row(vid=self._active_vid, first_event=view))

        # avoid first-line flicker by measuring immediately if mounted
        self._update_visible_row_height(self._active_vid)

    # ---------- prompt plumbing ----------

    def submit(self, text: str):
        print("SURFACE SUBMIT:", repr(text))

        # New command => user wants the newest message visible at the top
        self._request_scroll_to_top(force=True)

        # Enter = new try => free validation error
        self._assist_error = None

        if self.on_submit:
            self.on_submit(text)

        Clock.schedule_once(lambda _dt: setattr(self.ids.prompt, "focus", True), 0)

    def focus_prompt(self):
        self.ids.prompt.focus_input()

    def set_assist(self, text: str, state: str = "question") -> None:
        def _apply(_dt):
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
