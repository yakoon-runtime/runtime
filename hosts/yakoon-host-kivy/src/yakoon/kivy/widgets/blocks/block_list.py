from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

# ---------- Contracts (strict, no getattr/Any) ----------


class ListItemLike(Protocol):
    id: str | None
    head: str
    blocks: Sequence[object] | None


class ListBlockLike(Protocol):
    items: Sequence[ListItemLike]


# ---------- Widgets ----------


class StreamLabel(Label):
    def append_text(self, chunk: str) -> None:
        self.text = (self.text or "") + chunk
        # Height ist in KV an texture_size gebunden; optional trigger:
        self.texture_update()


class ListWidget(BoxLayout):

    level_indent = NumericProperty(0)
    indent_step = NumericProperty(9)

    def append_child(self, child) -> None:
        # propagate current level indent to items (helps nested lists)
        set_level_indent = getattr(child, "set_level_indent", None)
        if callable(set_level_indent):
            set_level_indent(int(self.level_indent), int(self.indent_step))
        self.add_widget(child)


class ListItemWidget(BoxLayout):

    level_indent = NumericProperty(0)
    body_indent = NumericProperty(18)

    def set_level_indent(self, level_indent: int, indent_step: int) -> None:
        self.level_indent = int(level_indent)
        self.body_indent = int(indent_step)

    def set_head(self, head: str) -> None:
        # KV defines the label; we only set content
        self.ids.head_label.text = f"• {head}"

    def append_child(self, child) -> None:
        # If a nested list comes in, increase its indent
        if isinstance(child, ListWidget):
            child.level_indent = int(self.level_indent + self.body_indent)
            child.indent_step = int(self.body_indent)
        self.ids.body.add_widget(child)


# ---------- Renderers ----------


@dataclass(slots=True)
class ListBlockRenderer:
    registry: object

    def render(self, block: ListBlockLike) -> ListWidget:
        return ListWidget()


@dataclass(slots=True)
class ListItemBlockRenderer:
    registry: object

    def render(self, block: ListItemLike) -> ListItemWidget:
        w = ListItemWidget()
        w.set_head(block.head)
        return w
