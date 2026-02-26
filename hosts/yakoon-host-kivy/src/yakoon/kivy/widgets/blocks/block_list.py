from dataclasses import dataclass
from typing import Any

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from yakoon.kivy.widgets.blocks.block_text import TextBlockWidget


def _inline_to_str(x: Any) -> str:
    # Minimal: InlineText/InlineCode/InlineLink -> str
    t = getattr(x, "type", None)
    if t == "text":
        return str(getattr(x, "text", "") or "")
    if t == "code":
        return str(getattr(x, "code", "") or "")
    if t == "link":
        txt = str(getattr(x, "text", "") or "")
        href = str(getattr(x, "href", "") or "")
        return f"{txt} ({href})" if href else txt
    return str(x)


def _head_to_str(head: Any) -> str:
    if head is None:
        return ""
    if isinstance(head, str):
        return head
    if isinstance(head, list):
        return "".join(_inline_to_str(i) for i in head)
    return str(head)


class ListWidget(BoxLayout):

    def __init__(self, indent_level: int = 0, indent_step: int = 18, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter("height"))
        self._indent_step = int(indent_step)
        self._indent_level = int(indent_level)
        self.padding = (dp(self._indent_level), 0, 0, 0)
        self.size_hint_x = 1

    def append_child(self, child):
        # propagate current level to list items (helps nested lists)
        if hasattr(child, "set_level_indent") and callable(child.set_level_indent):
            child.set_level_indent(self._indent_level, self._indent_step)
        self.add_widget(child)

    def set_indent(self, indent_level: int) -> None:
        self._indent_level = int(indent_level)
        self.padding = (dp(self._indent_level), 0, 0, 0)


class ListItemWidget(BoxLayout):

    def __init__(self, head_text="", indent_left=0, **kwargs):

        super().__init__(orientation="vertical", size_hint_y=None, **kwargs)
        self._level_indent = 0
        self._indent_step = 18
        self._indent_left = indent_left
        self.size_hint_x = 1

        self.bind(minimum_height=self.setter("height"))

        bullet = TextBlockWidget()
        bullet.text = f"• {head_text}"
        self.add_widget(bullet)

        self._body = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(self._indent_left), 0, 0, 0),
        )
        if not self._body.children:
            self._body.height = 0

        self._body.bind(minimum_height=self._body.setter("height"))
        self.add_widget(self._body)

    def set_level_indent(self, level_indent: int, indent_step: int) -> None:
        self._level_indent = int(level_indent)
        self._indent_step = int(indent_step)

    def append_child(self, child):
        # if a nested list comes in, increase its indent (classic list nesting)
        if isinstance(child, ListWidget):
            child.set_indent(self._level_indent + self._indent_step)
        self._body.add_widget(child)


@dataclass(slots=True)
class ListBlockRenderer:
    registry: Any

    def render(self, block: Any) -> Any:
        # snapshot fallback:
        root = ListWidget()

        items = getattr(block, "items", []) or []
        for item in items:
            head = str(getattr(item, "head", "") or "")
            item_widget = ListItemWidget(head_text=head)
            root.append_child(item_widget)

            nested = getattr(item, "blocks", None)
            if nested:
                for child in nested:
                    item_widget.append_child(self.registry.render(child))

        return root


@dataclass(slots=True)
class ListItemBlockRenderer:

    registry: Any

    def render(self, block: Any) -> Any:
        head = _head_to_str(getattr(block, "head", ""))
        w = ListItemWidget(head_text=head)

        # snapshot nested blocks (optional)
        nested = getattr(block, "blocks", None)
        if nested:
            for child in nested:
                w.append_child(self.registry.render(child))

        return w
