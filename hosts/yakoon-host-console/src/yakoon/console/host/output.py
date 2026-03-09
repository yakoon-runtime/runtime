from __future__ import annotations

from yakoon.base.ui import Block, FieldsBlock, ViewEvent


class ConsoleOutput:
    """
    Console renderer for the new document model.
    Renders view.blocks directly.
    """

    async def view(self, event: ViewEvent) -> None:
        text = self.render(event)
        if text:
            print(text)

    def render(self, event: ViewEvent) -> str:
        lines: list[str] = []

        if event.header:
            if event.header.role == "error":
                lines.append("(Status)")
            elif event.header.role == "info":
                lines.append("(Information)")

            if event.header.title:
                lines.append(event.header.title)
                lines.append("")

        for op in event.patch.ops:
            block = getattr(op, "block", None)
            if block:
                self._render_blocks(lines, [block], indent=0)

        return "\n".join(lines).rstrip()

    def _render_blocks(
        self,
        lines: list[str],
        blocks: list[Block],
        *,
        indent: int,
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
                for item in block.items:
                    lines.append(pad + f"{item.key}: {item.value}")
                    if item.blocks:
                        self._render_blocks(lines, item.blocks, indent=indent + 2)
                lines.append("")

            elif t == "rule":
                lines.append(pad + ("-" * 40))
                lines.append("")

            elif t == "spacer":
                for _ in range(block.size):
                    lines.append("")

            elif isinstance(block, FieldsBlock):
                if block.input_mode == "prompt":
                    continue

                title = block.title or "Eingabe"
                mode = block.input_mode
                lines.append(pad + f"[{title} - {mode}]")
                for fd in block.fields:
                    label = fd.title or fd.var or "field"
                    lines.append(pad + f"  • {label}")
                lines.append("")

    def _render_textish(self, value) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            return value

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

        return str(value)
