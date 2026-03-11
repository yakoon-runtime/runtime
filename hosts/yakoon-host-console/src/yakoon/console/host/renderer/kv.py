from .base import BaseRenderer


class KVRenderer(BaseRenderer):

    def render(self):
        lines = []

        items = self.node.props.get("items", [])

        for item in items:
            key = getattr(item, "key", "")
            value = getattr(item, "value", "")
            lines.append(f"{key}: {value}")

        lines.append("")
        return lines
