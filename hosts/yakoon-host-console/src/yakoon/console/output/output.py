# output.py

from __future__ import annotations

import asyncio

from yakoon.base.ui import (
    FlowControl,
    PatchAppendStructure,
    PatchAppendText,
    PatchReset,
    PerceptualStream,
    ViewEvent,
)
from yakoon.console.renderer import BaseRenderer, RendererBuilder


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

    def __init__(self, surface):
        self._flow: FlowControl
        self._nodes: dict[str, Node] = {}
        self._renderers: dict[str, BaseRenderer] = {}
        self._builder = RendererBuilder(surface)
        self._stream = PerceptualStream(self._append_text, self._finished)

        self._cancelled = False
        loop = asyncio.get_running_loop()
        loop.create_task(self._stream_loop())

    # PerceptualStream ---------------------------------

    async def _stream_loop(self):

        while not self._cancelled:
            self._stream.step(self._stream.FRAME_INTERVAL)
            await asyncio.sleep(0.005)

    def _append_text(self, node_id, key, chunk):

        renderer = self._renderers.get(node_id)
        if not renderer:
            return

        renderer.append(key, chunk)

    def _finished(self):
        self._flow.release()

    async def cancel(self):
        self._cancelled = True

    # IO ---------------------------------

    def set_flow_control(self, flow: FlowControl) -> None:
        self._flow = flow

    async def view(self, event: ViewEvent) -> None:

        for op in event.patch.ops:

            if isinstance(op, PatchReset):
                self._nodes.clear()
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
                    self._stream.push(op.block_id, op.key, op.text)
                    # print(op.block_id)
