from __future__ import annotations

from typing import Any

from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from yakoon.kivy.widgets.blocks.registry import BlockRendererRegistry


class CommandMessage(BoxLayout):
    """
    Renders a ViewSpec message either as a full snapshot (set_view)
    or incrementally via patch ops (apply_patch).

    Contract assumptions:
    - Block IDs are expected to be stable strings when streaming.
    - append_text targets an existing widget by id (or alias id).
    - append_child attaches a rendered child widget to a container parent.
    """

    def __init__(self, registry: BlockRendererRegistry | None = None, **kw: Any):
        super().__init__(**kw)

        self.orientation = "vertical"
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))

        self._registry = registry or BlockRendererRegistry(dbg=True)
        self._view: Any | None = None

        # patch state: id -> widget (plus optional alias ids, e.g. "<item>.head")
        self._widgets_by_id: dict[str, Any] = {}

    @property
    def view(self) -> Any | None:
        return self._view

    # ---------- internal helpers ----------

    def _reset(self) -> None:
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
        # Prefer explicit streaming API if present
        append_child = getattr(parent, "append_child", None)
        if callable(append_child):
            append_child(child_widget)
            return

        # Fallback: Kivy container interface
        add_widget = getattr(parent, "add_widget", None)
        if callable(add_widget):
            add_widget(child_widget)
            return

        # Not a container -> ignore (or raise if you want strict mode)

    def _maybe_register_stream_aliases(self, block: Any, widget: Any) -> None:
        """
        Register alias targets for streaming sub-parts.

        - list_item: "<id>.head"
        - kv_item:   "<id>.value"
        """
        btype = getattr(block, "type", None)
        bid = getattr(block, "id", None)

        if not isinstance(bid, str) or not bid:
            return

        # -----------------------------
        # list_item -> head alias
        # -----------------------------
        if btype == "list_item":
            children = getattr(widget, "children", None)
            if not children:
                return

            # ListItemWidget: bullet is last child (Kivy reverse order)
            bullet = children[-1]
            self._register(f"{bid}.head", bullet)
            return

        # -----------------------------
        # kv_item -> value alias
        # -----------------------------
        if btype == "kv_item":
            # KvItemWidget should expose value_widget()
            getter = getattr(widget, "value_widget", None)
            if callable(getter):
                self._register(f"{bid}.value", getter())
            return

    # ---------- Non-stream rendering (full view) ----------

    def set_view(self, view: Any) -> None:
        """Render a full, non-streaming view (snapshot)."""
        self._view = view
        self._reset()

        msg = getattr(view, "message", None) if view else None
        blocks = list(getattr(msg, "blocks", None) or []) if msg else []
        for b in blocks:
            w = self._render_block(b)
            self.add_widget(w)
            self._register(getattr(b, "id", None), w)

    # ---------- Streaming (patch ops) ----------

    def apply_patch(self, patch: Any) -> None:
        """Apply streaming patch ops in-place."""
        if patch is None:
            return

        for op in patch.ops or []:
            kind = getattr(op, "op", None)

            if kind == "reset":
                self._reset()
                continue

            if kind == "append_block":
                block = getattr(op, "block", None)
                if block is None:
                    continue

                bid = getattr(block, "id", None)
                if not isinstance(bid, str) or not bid:
                    # IDs are required for stable streaming; ignore invalid blocks
                    continue

                w = self._render_block(block)
                self.add_widget(w)
                self._register(bid, w)
                continue

            if kind == "append_text":
                target_id = getattr(op, "block_id", None)
                chunk = getattr(op, "text", "") or ""
                w = self._lookup(target_id)
                if w is None:
                    continue

                # Expect TextBlockWidget-like API
                w.text = (getattr(w, "text", "") or "") + chunk
                continue

            if kind == "append_child":
                # preferred fields: parent_id + block
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
                continue

            # Unknown op -> ignore (forward compatible)

    def dispose(self) -> None:
        # Placeholder for future cleanup hooks
        pass


Factory.register("CommandMessage", cls=CommandMessage)
