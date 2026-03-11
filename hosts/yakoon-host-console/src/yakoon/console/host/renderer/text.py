from .base import BaseRenderer


class TextRenderer(BaseRenderer):

    def render(self):
        text = self.node.text.get("text")
        if not text:
            return []

        return [text, ""]
