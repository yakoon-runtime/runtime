from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget


class HeaderBlockLike(Protocol):
    role: str | None
    title: str | None
    subtitle: str | None


class HeaderBlockWidget(BoxLayout):
    """
    Document header widget for one message/document.

    Not a UI contract block.
    This is a Kivy-side renderer target for ViewHeader.
    """

    def set_header(
        self,
        *,
        role: str | None,
        title: str | None,
        subtitle: str | None,
    ) -> None:
        ids = getattr(self, "ids", {})

        role_label = ids.get("role_label")
        title_label = ids.get("title_label")
        subtitle_label = ids.get("subtitle_label")

        if role_label is not None:
            role_label.text = self._role_text(role)

        if title_label is not None:
            title_label.text = title or ""

        if subtitle_label is not None:
            subtitle_label.text = subtitle or ""

        self._reflow()

    def _role_text(self, role: str | None) -> str:
        if role == "info":
            return "Information"
        if role == "error":
            return "Status"
        if role == "warning":
            return "Warnung"
        if role == "success":
            return "Erfolg"
        if role == "help":
            return "Hilfe"
        return ""

    def _reflow(self, *_: object) -> None:
        self.do_layout()
        min_h = 0
        for child in self.children:
            if hasattr(child, "texture_update"):
                child.texture_update()
            h = (
                getattr(child, "texture_size", [0, 0])[1]
                if hasattr(child, "texture_size")
                else child.height
            )
            min_h += max(h, getattr(child, "height", 0))
        self.height = max(min_h + dp(10), dp(24))


@dataclass(slots=True)
class HeaderBlockRenderer:
    """
    Adapter: ViewHeader -> HeaderBlockWidget
    """

    def render(self, block: HeaderBlockLike) -> Widget:
        w = HeaderBlockWidget()
        w.set_header(
            role=getattr(block, "role", None),
            title=getattr(block, "title", None),
            subtitle=getattr(block, "subtitle", None),
        )
        return w
