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
                print(b)
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
                # später
                bid = getattr(op, "block_id", None)
                row = getattr(op, "row", None)
                w = self._widgets_by_id.get(bid) if bid else None
                if (
                    w is not None
                    and hasattr(w, "append_child")
                    and callable(w.append_child)
                ):
                    w.append_child(row)

    def dispose(self) -> None:
        pass


Factory.register("CommandMessage", cls=CommandMessage)
