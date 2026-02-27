from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from yakoon.kivy.widgets.blocks.block import DebugBackgroundMixin
from yakoon.kivy.widgets.blocks.block_text import TextBlockWidget


class KvWidget(BoxLayout):
    """
    kv = 2-column key/value container (modern UI layout, value streamable)
    - Key width is derived from longest key, but clamped to max_key_ratio * container width.
    """

    def __init__(
        self,
        *,
        max_key_ratio: float = 0.40,
        min_key_dp: float = 80,
        max_key_dp: float = 360,
        row_spacing_dp: float = 6,
        **kwargs: Any,
    ):
        super().__init__(orientation="vertical", size_hint_y=None, **kwargs)
        self.size_hint_x = 1  # critical: stable width propagation (prevents wrap jumps)
        self.bind(minimum_height=self.setter("height"))

        self.spacing = dp(row_spacing_dp)

        self.size_hint_x = 1
        self.size_hint_y = None

        self._max_key_ratio = float(max_key_ratio)
        self._min_key_px = dp(min_key_dp)
        self._max_key_px = dp(max_key_dp)

        self._items: list[KvItemWidget] = []

        # Recompute when our width changes (ratio clamp depends on available width)
        self.bind(width=lambda *_: self._recompute_key_width())

    def append_child(self, child: Widget) -> None:
        # Container streaming API
        if isinstance(child, KvItemWidget):
            self._items.append(child)
            # If the key text changes later (rare), item can call parent recompute; still safe:
            child._on_key_measured = self._recompute_key_width
        self.add_widget(child)
        self._recompute_key_width()

    def _recompute_key_width(self) -> None:
        if not self._items:
            return

        # measure longest key label
        measured = 0.0
        for it in self._items:
            measured = max(measured, it.measured_key_width())

        # clamp by available width * ratio, and absolute min/max
        available = max(0.0, float(self.width))
        ratio_cap = available * self._max_key_ratio

        target = min(measured, ratio_cap)
        target = max(target, self._min_key_px)
        target = min(target, self._max_key_px)

        for it in self._items:
            it.set_key_width(target)


class KvItemWidget(DebugBackgroundMixin, BoxLayout):
    """
    kv_item = single key/value row; value may contain text or nested blocks
    Value streaming alias: "<item_id>.value" (registered by CommandMessage via widget structure).
    """

    def __init__(self, key_text: str = "", value_text: str = "", **kwargs: Any):
        super().__init__(orientation="vertical", size_hint_y=None, **kwargs)

        self._dbg_bg()

        self.size_hint_x = 1
        self.size_hint_y = None

        self.bind(minimum_height=self.setter("height"))
        self._on_key_measured = None  # set by parent KvWidget if present

        # Row: key | value
        row = BoxLayout(orientation="horizontal", size_hint_y=None)
        row.size_hint_x = 1
        row.size_hint_y = None
        row.bind(minimum_height=row.setter("height"))

        self._key = TextBlockWidget()
        self._key.size_hint_x = None  # fixed width set by KvWidget
        self._key.size_hint_y = None
        self._key.text = str(key_text or "")
        # ensure key label measures its texture
        self._key.bind(texture_size=lambda *_: self._notify_key_measured())

        self._value = TextBlockWidget()
        self._value.size_hint_x = 1
        self._value.size_hint_y = None

        self._value.text = str(value_text or "")

        row.add_widget(self._key)
        row.add_widget(self._value)
        self.add_widget(row)

        # Optional body for nested blocks under the row (spans full width)
        self._body = BoxLayout(
            orientation="vertical", size_hint_y=None, padding=(dp(18), 0, 0, 0)
        )
        self._body.size_hint_x = 1
        self._body.size_hint_y = None
        self._body.bind(minimum_height=self._body.setter("height"))
        self.add_widget(self._body)

    def measured_key_width(self) -> float:
        # texture_size[0] is the measured width of rendered key text
        try:
            w = float(self._key.texture_size[0])
        except Exception:
            w = 0.0
        # add a little breathing room
        return w + dp(12)

    def set_key_width(self, width_px: float) -> None:
        self._key.width = float(width_px)

    def value_widget(self) -> Widget:
        # For alias registration "<id>.value"
        return self._value

    def append_child(self, child: Widget) -> None:
        self._body.add_widget(child)

    def _notify_key_measured(self) -> None:
        cb = self._on_key_measured
        if callable(cb):
            cb()


# -----------------------------
# Renderers
# -----------------------------


@dataclass(slots=True)
class KvBlockRenderer:
    registry: Any  # BlockRendererRegistry (duck typing)

    def render(self, block: Any) -> Widget:
        root = KvWidget()

        items: Iterable[Any] = getattr(block, "items", []) or []
        for it in items:
            key = str(getattr(it, "key", "") or "")
            value = getattr(it, "value", None)

            # Snapshot behavior:
            # - if value is str -> put into value label
            # - if value is list (blocks) -> keep value empty and append blocks into body
            if isinstance(value, str):
                row = KvItemWidget(key_text=key, value_text=value)
            else:
                row = KvItemWidget(key_text=key, value_text="")

            # Snapshot nested blocks (optional)
            if isinstance(value, list):
                for child in value:
                    row.append_child(self.registry.render(child))

            # Also allow explicit nested blocks field (future-proof)
            nested = getattr(it, "blocks", None)
            if nested:
                for child in nested:
                    row.append_child(self.registry.render(child))

            root.append_child(row)

        return root


@dataclass(slots=True)
class KvItemBlockRenderer:
    registry: Any  # BlockRendererRegistry (duck typing)

    def render(self, block: Any) -> Widget:
        key = str(getattr(block, "key", "") or "")
        value = getattr(block, "value", None)

        if isinstance(value, str):
            w = KvItemWidget(key_text=key, value_text=value)
        else:
            w = KvItemWidget(key_text=key, value_text="")

        # Snapshot nested blocks
        if isinstance(value, list):
            for child in value:
                w.append_child(self.registry.render(child))

        nested = getattr(block, "blocks", None)
        if nested:
            for child in nested:
                w.append_child(self.registry.render(child))

        return w
