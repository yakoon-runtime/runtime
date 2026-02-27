from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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
    Behavior-only: supports PatchAppendText targets.
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

    def _reflow(self, *_: object) -> None:
        # IMPORTANT: text_size is layout (KV); here we only do the "compute height" part.
        self.texture_update()
        self.height = self.texture_size[1] + dp(6)

    def append_text(self, chunk: str) -> None:
        self.text = (self.text or "") + chunk
        self._reflow()


@dataclass(slots=True)
class TextBlockRenderer:
    """
    Adapter: block -> widget. No fallbacks. If the block is invalid,
    that is a parser/contract bug and should fail loudly.
    """

    def render(self, block: TextBlockLike) -> Widget:
        w = TextBlockWidget()
        w.text = str(block.text)
        w._reflow()  # ensures correct height on first render
        return w
