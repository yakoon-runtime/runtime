# output.py

from __future__ import annotations

from yakoon.base.ui import (
    PatchAppendStructure,
    PatchAppendText,
    PatchReset,
    ViewEvent,
)

from .builder import RendererBuilder


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
        self._builder = RendererBuilder()

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

            renderer = self._builder.create(node)
            if not renderer:
                continue

            lines.extend(renderer.render())

        return "\n".join(lines).rstrip()

    def find_prompt_block(self):
        for node in self._nodes.values():
            if node.type != "fields":
                continue

            block = node.props.get("block")
            if block and block.input_mode == "prompt":
                return block

        return None
