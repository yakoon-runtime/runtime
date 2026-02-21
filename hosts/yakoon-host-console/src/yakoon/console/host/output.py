from __future__ import annotations

from yakoon.base.models.view import MessageSpec, ViewSpec  # pfade anpassen


class ConsoleOutput:
    """
    Console renderer (typed, view-only).
    Renders only view.message. Ignores view.input (handled by Host).
    """

    async def view(self, view: ViewSpec) -> None:
        text = self.render(view)
        if text:
            print(text)

    def render(self, view: ViewSpec) -> str:
        msg = view.message
        if msg is None:
            return ""

        prefix = ""
        if msg.role == "error":
            prefix = "(Status) "
        if msg.role == "info":
            prefix = "(Information) "

        body = self._render_message(msg)
        if not body:
            return ""

        return prefix + body

    def _render_message(self, msg: MessageSpec) -> str:
        lines: list[str] = []

        if msg.title:
            lines.append(str(msg.title))
            lines.append("")

        for block in msg.blocks or []:
            t = getattr(block, "type", None)

            if t == "text":
                lines.append(str(getattr(block, "text", "")))
                lines.append("")

            elif t == "list":
                for item in getattr(block, "items", []) or []:
                    lines.append(f"- {item}")
                lines.append("")

            elif t == "kv":
                items = getattr(block, "items", []) or []
                for k, v in items:
                    lines.append(f"{k}: {v}")
                lines.append("")

        return "\n".join(lines).rstrip()
