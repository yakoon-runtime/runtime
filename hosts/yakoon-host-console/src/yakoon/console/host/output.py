# output.py

from __future__ import annotations

import asyncio
import sys

from yakoon.base.ui import (
    PatchAppendStructure,
    PatchAppendText,
    PatchReset,
    PerceptualStream,
    RenderDone,
    ViewEvent,
)
from yakoon.console.host.renderer.base import BaseRenderer

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
        self._renderers: dict[str, BaseRenderer] = {}
        self._builder = RendererBuilder()
        self._stream = PerceptualStream(self._append_text, self._finish_line)
        asyncio.create_task(self._stream.render_loop())

    # PerceptualStream ---------------------------------

    def _append_text(self, node_id, key, chunk):

        renderer = self._renderers.get(node_id)
        if not renderer:
            return

        renderer.append(key, chunk)

    def _finish_line(self):
        sys.stdout.write("\n")
        sys.stdout.flush()

    # ---------------------------------

    async def view(self, event: ViewEvent, done: RenderDone) -> None:

        self._apply_patch(event)
        if event.patch.final:
            self._stream.finish()

    def _apply_patch(self, event: ViewEvent) -> None:

        for op in event.patch.ops:

            if isinstance(op, PatchReset):
                self._nodes.clear()
                self._stream.reset()
                self._renderers.clear()

            elif isinstance(op, PatchAppendStructure):
                for spec in op.nodes:

                    node = Node(
                        id=spec.id,
                        type=spec.type,
                        parent=spec.parent,
                        props=spec.props,
                    )

                    self._nodes[spec.id] = node
                    renderer = self._builder.create(node)
                    self._renderers[node.id] = renderer

            elif isinstance(op, PatchAppendText):
                node = self._nodes.get(op.block_id)
                if node:
                    self._stream.push(op.block_id, node.type, op.text)
