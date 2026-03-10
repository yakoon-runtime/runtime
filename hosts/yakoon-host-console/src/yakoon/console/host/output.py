# output.py

from __future__ import annotations

from yakoon.base.ui import (
    PatchAppendStructure,
    PatchAppendText,
    PatchReset,
    ViewEvent,
)


class Node:
    def __init__(self, *, id: str, type: str, parent: str | None, props: dict):
        self.id = id
        self.type = type
        self.parent = parent
        self.props = props
        self.text: dict[str, str] = {}


class ConsoleOutput:
    """
    Console renderer for streaming document model.
    """

    def __init__(self):
        self._nodes: dict[str, Node] = {}

    async def view(self, event: ViewEvent) -> None:
        self._apply_patch(event)
        text = self.render(event)
        if text:
            print(text)

    def _apply_patch(self, event: ViewEvent) -> None:
        for op in event.patch.ops:

            if isinstance(op, PatchReset):
                self._nodes.clear()

            elif isinstance(op, PatchAppendStructure):
                for spec in op.nodes:
                    self._nodes[spec.id] = Node(
                        id=spec.id,
                        type=spec.type,
                        parent=spec.parent,
                        props=spec.props,
                    )

            elif isinstance(op, PatchAppendText):
                node = self._nodes.get(op.block_id)
                if not node:
                    continue

                buf = node.text.setdefault(op.key, "")
                node.text[op.key] = buf + op.text

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

        for node in self._nodes.values():

            if node.type == "text":
                text = node.text.get("text")
                if text:
                    lines.append(text)
                    lines.append("")

            elif node.type == "rule":
                lines.append("-" * 40)
                lines.append("")

            elif node.type == "spacer":
                size = node.props.get("size", 1)
                for _ in range(size):
                    lines.append("")

            elif node.type == "list":
                items = node.props.get("items", [])
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

            elif node.type == "kv":
                items = node.props.get("items", [])
                for item in items:
                    key = getattr(item, "key", "")
                    value = getattr(item, "value", "")
                    lines.append(f"{key}: {value}")

                lines.append("")

        return "\n".join(lines).rstrip()

    def find_prompt_block(self):
        for node in self._nodes.values():
            if node.type != "fields":
                continue

            block = node.props.get("block")
            if block and block.input_mode == "prompt":
                return block

        return None
