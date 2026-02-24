from __future__ import annotations

from yakoon.base.models.message import Block
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
        # title etc...
        self._render_blocks(lines, msg.blocks or [], indent=0)
        return "\n".join(lines).rstrip()

    def _render_blocks(
        self, lines: list[str], blocks: list[Block], *, indent: int
    ) -> None:
        pad = " " * indent

        for block in blocks:
            t = getattr(block, "type", None)

            if t == "text":
                lines.append(pad + self._render_textish(block.text))
                lines.append("")

            elif t == "list":
                for item in block.items:
                    lines.append(pad + "- " + self._render_textish(item.head))
                    if item.blocks:
                        self._render_blocks(lines, item.blocks, indent=indent + 2)
                lines.append("")

            elif t == "kv":
                for k, v in block.items:
                    lines.append(pad + f"{k}: {v}")
                lines.append("")

            elif t == "rule":
                lines.append(pad + ("-" * 40))
                lines.append("")

            elif t == "spacer":
                for _ in range(block.size):
                    lines.append("")

    def _render_textish(self, value) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            return value

        # Inline-Liste?
        if isinstance(value, list):
            parts: list[str] = []
            for inl in value:
                t = getattr(inl, "type", None)
                if t == "text":
                    parts.append(getattr(inl, "text", ""))
                elif t == "code":
                    parts.append(f"`{getattr(inl, 'code', '')}`")
                elif t == "link":
                    text = getattr(inl, "text", "")
                    href = getattr(inl, "href", "")
                    parts.append(f"{text} ({href})")
                else:
                    parts.append("")
            return "".join(parts)

        # Fallback: int/float/bool/… => stringifizieren
        return str(value)
