from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

# -----------------------------
# Contracts
# -----------------------------


class KvItemLike(Protocol):
    id: str | None
    key: str
    value: Any


class KvBlockLike(Protocol):
    id: str | None
    items: Iterable[KvItemLike]


# -----------------------------
# Widgets (UI-only, layout in KV)
# -----------------------------


class KvWidget(BoxLayout):
    max_key_ratio = NumericProperty(0.30)
    min_key_dp = NumericProperty(80)
    max_key_dp = NumericProperty(260)

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._items: list[KvItemWidget] = []
        self.bind(width=lambda *_: self._recompute_key_width())

    def append_child(self, child: Widget) -> None:
        if isinstance(child, KvItemWidget):
            self._items.append(child)
            child._on_key_measured = self._recompute_key_width
        self.add_widget(child)
        self._recompute_key_width()

    def _recompute_key_width(self) -> None:
        if not self._items:
            return

        measured = 0.0
        for it in self._items:
            measured = max(measured, it.measured_key_width())

        available = max(0.0, float(self.width))
        ratio_cap = available * float(self.max_key_ratio)

        target = min(measured, ratio_cap)
        target = max(target, float(dp(self.min_key_dp)))
        target = min(target, float(dp(self.max_key_dp)))

        for it in self._items:
            it.set_key_width(target)


class KvItemWidget(BoxLayout):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._on_key_measured = None

    def on_kv_post(self, base_widget):
        key = self.ids.get("key_label")
        if key:
            key.bind(texture_size=lambda *_: self._notify_key_measured())

    def set_key(self, text: str) -> None:
        self.ids.key_label.text = text or ""

    def set_value(self, text: str) -> None:
        self.ids.value_label.text = text or ""

    def measured_key_width(self) -> float:
        key = self.ids.get("key_label")
        if not key:
            return 0.0
        try:
            w = float(key.texture_size[0])
        except Exception:
            w = 0.0
        return w + dp(12)

    def set_key_width(self, width_px: float) -> None:
        self.ids.key_label.width = float(width_px)

    def value_widget(self) -> Widget:
        return self.ids.value_label

    def append_child(self, child: Widget) -> None:
        self.ids.body.add_widget(child)

    def _notify_key_measured(self) -> None:
        cb = self._on_key_measured
        if callable(cb):
            cb()

    # Streaming support
    def append_value_text(self, chunk: str) -> None:
        lbl = self.ids.get("value_label")
        if lbl:
            lbl.text = (lbl.text or "") + chunk
            lbl.texture_update()


# -----------------------------
# Renderers (container-only)
# -----------------------------


@dataclass(slots=True)
class KvBlockRenderer:
    registry: Any

    def render(self, block: KvBlockLike) -> Widget:
        return KvWidget()


@dataclass(slots=True)
class KvItemBlockRenderer:
    registry: Any

    def render(self, block: KvItemLike) -> Widget:
        w = KvItemWidget()
        w.set_key(str(block.key or ""))
        w.set_value("")  # streaming-first
        return w
