from .base import BaseInlineRenderer


class BreakInlineRenderer(BaseInlineRenderer):

    def render(self) -> str:
        return "\n"
