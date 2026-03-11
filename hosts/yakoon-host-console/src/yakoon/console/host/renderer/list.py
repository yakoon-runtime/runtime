from .base import BaseRenderer


class ListRenderer(BaseRenderer):

    def render(self):
        lines = []

        items = self.node.props.get("items", [])

        for item in items:
            head = getattr(item, "head", "")
            if head:
                lines.append(f"- {head}")

            if getattr(item, "blocks", None):
                for sub in item.blocks:
                    text = getattr(sub, "text", "")
                    if text:
                        lines.append(f"  {text}")

        lines.append("")
        return lines
