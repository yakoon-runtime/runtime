from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class TextBlockLike(Protocol):
    """
    Platform contract: TextBlock has a 'text' field.
    Keep this minimal and stable.
    """

    text: str


class StreamLabel(Label):
    """
    Behavior-only: supports  targets.
    Styling stays in KV.
    """

    def append_text(self, chunk: str) -> None:
        self.text = (self.text or "") + (chunk or "")
        # ensure texture_size is current for auto-height rules in KV
        self.texture_update()


class TextBlockWidget(Label):
    """
    UI behavior only:
    - auto-height based on texture
    - reflow method called by KV bindings (or optional callers)
    """

    def __init__(self, **kw):
        super().__init__(**kw)

        self.size_hint_y = None

        # Reflow wenn Breite oder Text sich ändern
        self.bind(width=self._reflow)
        self.bind(text=self._reflow)
        self._trigger_reflow = Clock.create_trigger(self._reflow, 0)

    def _reflow(self, *_):

        self.text_size = (self.width, None)
        self.texture_update()
        self.height = self.texture_size[1] + dp(6)

    def append_text(self, key: str, chunk: str):

        if key != "text":
            return

        self.text = (self.text or "") + chunk

        self._reflow()
        # self._trigger_reflow()


@dataclass(slots=True)
class TextBlockRenderer:
    """
    Adapter: block -> widget. No fallbacks. If the block is invalid,
    that is a parser/contract bug and should fail loudly.
    """

    def render(self, node) -> Widget:
        return TextBlockWidget()
