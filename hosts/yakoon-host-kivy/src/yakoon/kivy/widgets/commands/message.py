from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kivy.factory import Factory
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.stacklayout import StackLayout
from yakoon.base.ui.blocks import TextBlock
from yakoon.kivy.widgets.blocks.registry import BlockRendererRegistry


@dataclass(slots=True)
class MessageModel:
    vid: str
    header: Any | None
    events: list[Any]  # ViewEvent only


class CommandMessage(RecycleDataViewBehavior, StackLayout):
    def __init__(self, registry: BlockRendererRegistry | None = None, **kw: Any):
        super().__init__(**kw)
        self.size_hint_y = None
        self._registry = registry or BlockRendererRegistry(dbg=True)
        self._widgets_by_id: dict[str, Any] = {}
        self._vid: str | None = None
        self._applied_n: int = 0
        self._current_header: Any | None = None

    def refresh_view_attrs(self, rv, index, data):
        vid = data.get("vid")
        events = data.get("events") or []
        header = data.get("header")

        if vid != self._vid:
            self._vid = vid
            self._applied_n = 0
            self._current_header = header
            self._clear_content()
            self._render_header(header)
        elif header is not self._current_header:
            self._current_header = header
            self._clear_content()
            self._applied_n = 0
            self._render_header(header)

        if self._applied_n >= len(events):
            return super().refresh_view_attrs(rv, index, data)

        for ev in events[self._applied_n :]:
            patch = getattr(ev, "patch", None)
            if patch is not None:
                self.apply_patch(patch)

        self._applied_n = len(events)
        return super().refresh_view_attrs(rv, index, data)

    def get_calc_height(self):
        return sum(w.height for w in self.children)

    def _clear_content(self) -> None:
        self.clear_widgets()
        self._widgets_by_id.clear()

    def _register(self, wid: str | None, widget: Any) -> None:
        if isinstance(wid, str) and wid:
            self._widgets_by_id[wid] = widget

    def _lookup(self, wid: str | None) -> Any | None:
        if not isinstance(wid, str) or not wid:
            return None
        return self._widgets_by_id.get(wid)

    def _render_block(self, block: Any) -> Any:
        return self._registry.render(block)

    def _attach_child(self, parent: Any, child_widget: Any) -> None:
        append_child = getattr(parent, "append_child", None)
        if callable(append_child):
            append_child(child_widget)
            return

        add_widget = getattr(parent, "add_widget", None)
        if callable(add_widget):
            add_widget(child_widget)

    def _maybe_register_stream_aliases(self, block: Any, widget: Any) -> None:
        btype = getattr(block, "type", None)
        bid = getattr(block, "id", None)

        if not isinstance(bid, str) or not bid:
            return

        if btype == "list_item":
            ids = getattr(widget, "ids", None)
            head = ids.get("head_label") if isinstance(ids, dict) else None
            if head is not None:
                self._register(f"{bid}.head", head)
            return

        if btype == "kv_item":
            getter = getattr(widget, "value_widget", None)
            if callable(getter):
                self._register(f"{bid}.value", getter())

    def _header_text(self, header: Any | None) -> str:
        if header is None:
            return ""

        role = getattr(header, "role", None)
        title = getattr(header, "title", None)
        subtitle = getattr(header, "subtitle", None)

        parts: list[str] = []
        if role == "info":
            parts.append("(Information)")
        elif role == "error":
            parts.append("(Status)")
        elif role == "warning":
            parts.append("(Warnung)")
        elif role == "success":
            parts.append("(Erfolg)")
        elif role == "help":
            parts.append("(Hilfe)")

        if title:
            parts.append(title)
        if subtitle:
            parts.append(subtitle)

        return "\n".join(parts).strip()

    def _render_header(self, header: Any | None) -> None:
        text = self._header_text(header)
        if not text or self._vid is None:
            return

        block = TextBlock(
            id=f"{self._vid}:header",
            type="text",
            text=text,
        )
        widget = self._render_block(block)
        self.add_widget(widget)
        self._register(block.id, widget)

    def apply_patch(self, patch: Any) -> None:
        if patch is None:
            return

        for op in getattr(patch, "ops", None) or []:
            kind = getattr(op, "op", None)

            if kind == "reset":
                self._clear_content()
                self._render_header(self._current_header)
                continue

            if kind == "append_block":
                block = getattr(op, "block", None)
                if block is None:
                    continue

                bid = getattr(block, "id", None)
                if not isinstance(bid, str) or not bid:
                    continue

                widget = self._render_block(block)
                self.add_widget(widget)
                self._register(bid, widget)
                self._maybe_register_stream_aliases(block, widget)
                continue

            if kind == "append_text":
                target_id = getattr(op, "block_id", None)
                chunk = getattr(op, "text", "") or ""
                widget = self._lookup(target_id)
                if widget is None:
                    continue

                append = getattr(widget, "append_text", None)
                if not callable(append):
                    raise TypeError(
                        f"Target '{target_id}' does not support append_text()"
                    )
                append(chunk)
                continue

            if kind == "append_child":
                parent_id = getattr(op, "parent_id", None) or getattr(
                    op, "block_id", None
                )
                child_block = (
                    getattr(op, "block", None)
                    or getattr(op, "child", None)
                    or getattr(op, "row", None)
                )

                parent = self._lookup(parent_id)
                if parent is None or child_block is None:
                    continue

                child_widget = self._render_block(child_block)

                child_id = getattr(child_block, "id", None)
                if isinstance(child_id, str) and child_id:
                    self._register(child_id, child_widget)
                    self._maybe_register_stream_aliases(child_block, child_widget)

                self._attach_child(parent, child_widget)

    def dispose(self) -> None:
        pass


Factory.register("CommandMessage", cls=CommandMessage)
