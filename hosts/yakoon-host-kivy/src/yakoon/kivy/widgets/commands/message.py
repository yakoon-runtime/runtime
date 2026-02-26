from __future__ import annotations

from typing import Any

from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from yakoon.kivy.services.registry import BlockRendererRegistry


class CommandMessage(BoxLayout):

    def __init__(self, registry: BlockRendererRegistry | None = None, **kw):
        super().__init__(**kw)

        self.orientation = "vertical"
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))

        self._registry = registry or BlockRendererRegistry(dbg=True)
        self._view = None

        # patch state
        self._widgets_by_id: dict[str, Any] = {}

    @property
    def view(self):
        return self._view

    # ---------- Non-stream rendering (full view) ----------
    def set_view(self, view) -> None:
        """Render a full, non-streaming view."""
        self._view = view
        self.clear_widgets()
        self._widgets_by_id.clear()

        msg = getattr(view, "message", None) if view else None
        blocks = list(getattr(msg, "blocks", None) or []) if msg else []
        if not blocks:
            return

        for b in blocks:
            w = self._registry.render(b)
            self.add_widget(w)

            bid = getattr(b, "id", None)
            if bid:
                self._widgets_by_id[bid] = w

    # ---------- Streaming (patch ops) ----------
    def apply_patch(self, patch) -> None:
        """Apply streaming ops in-place."""
        if patch is None:
            return

        for op in patch.ops or []:
            kind = getattr(op, "op", None)

            if kind == "reset":
                self.clear_widgets()
                self._widgets_by_id.clear()

            elif kind == "append_block":
                b = getattr(op, "block", None)
                if b is None:
                    continue
                bid = getattr(b, "id", None)
                if not bid:
                    # IDs sind bei euch jetzt Pflicht -> wenn doch None, skip statt crash
                    continue

                w = self._registry.render(b)
                self.add_widget(w)
                self._widgets_by_id[bid] = w

            elif kind == "append_text":
                bid = getattr(op, "block_id", None)
                chunk = getattr(op, "text", "")
                if not bid:
                    continue

                w = self._widgets_by_id.get(bid)
                if w is None:
                    continue

                w.text = (w.text or "") + chunk

            elif kind == "append_child":
                # Generic container streaming:
                # op.parent_id (preferred) OR op.block_id (legacy) identifies the parent widget
                # op.block (preferred) OR op.child/row (legacy) is the child block to render+append
                parent_id = getattr(op, "parent_id", None) or getattr(
                    op, "block_id", None
                )
                child_block = (
                    getattr(op, "block", None)
                    or getattr(op, "child", None)
                    or getattr(op, "row", None)
                )

                if not parent_id or child_block is None:
                    continue

                parent = self._widgets_by_id.get(parent_id)
                if parent is None:
                    continue

                child_widget = self._registry.render(child_block)

                # register child id (critical for append_text later)
                child_id = getattr(child_block, "id", None)
                if child_id:
                    self._widgets_by_id[child_id] = child_widget

                    # list_item: also register "<id>.head" to the bullet TextBlockWidget
                    if getattr(child_block, "type", None) == "list_item":
                        if hasattr(child_widget, "children") and child_widget.children:
                            bullet = child_widget.children[-1]  # first added
                            self._widgets_by_id[f"{child_id}.head"] = bullet

                # attach to parent
                if hasattr(parent, "append_child") and callable(parent.append_child):
                    parent.append_child(child_widget)
                elif hasattr(parent, "add_widget") and callable(parent.add_widget):
                    parent.add_widget(child_widget)
                else:
                    # parent is not a container
                    continue

    def dispose(self) -> None:
        pass


Factory.register("CommandMessage", cls=CommandMessage)
