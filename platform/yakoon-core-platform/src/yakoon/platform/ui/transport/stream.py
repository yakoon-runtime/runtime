from __future__ import annotations

import re
import time
from collections.abc import Iterator
from dataclasses import dataclass

from yakoon.base.ui import (
    Block,
    EffectiveStreaming,
    OutputStreaming,
    OutputStreamPolicy,
    PatchAppendStructure,
    PatchAppendText,
    PatchFinishNode,
    View,
)
from yakoon.platform.runtime import Session
from yakoon.platform.ui import ViewEmitter, ViewTraversal

_WS = re.compile(r"\S+|\s+")


def iter_chunks(text: str, min_size: int, max_size: int) -> Iterator[str]:
    tokens = _WS.findall(text)
    buf = ""

    for tok in tokens:

        if len(tok) > max_size:
            if buf:
                yield buf
                buf = ""

            for i in range(0, len(tok), max_size):
                yield tok[i : i + max_size]

            continue

        if buf and len(buf) + len(tok) > max_size:
            yield buf
            buf = tok
            continue

        buf += tok

        if len(buf) >= min_size:
            yield buf
            buf = ""

    if buf:
        yield buf


@dataclass
class _ViewStream:
    session: Session
    view_id: str
    interval: float

    event_queue: list

    node_depth: dict[str, int]
    published_nodes: set[str]

    last_flush: float


class DefaultOutputStreamService:

    MIN_INTERVAL = 0.05
    MAX_INTERVAL = 0.25

    MIN_CHUNK_SIZE = 8
    MAX_CHUNK_SIZE = 96

    BATCH_SIZE = 64

    def __init__(self) -> None:
        self._streams: dict[str, _ViewStream] = {}
        self._traversal = ViewTraversal()
        self._emitter = ViewEmitter()

    # ---------------------------------------------------------

    def effective(
        self,
        base: OutputStreamPolicy,
        override: OutputStreaming | None,
    ) -> EffectiveStreaming:
        return self._effective(base, override)

    # ---------------------------------------------------------

    async def begin_view(
        self,
        session: Session,
        view: View,
        *,
        override: OutputStreaming | None = None,
    ) -> None:

        policy = session.get_output_stream_policy()

        vid = override.id if override and override.id else view.id
        assert vid is not None

        interval = max(self.MIN_INTERVAL, min(policy.interval, self.MAX_INTERVAL))

        stream = _ViewStream(
            session=session,
            view_id=vid,
            interval=interval,
            event_queue=[],
            node_depth={},
            published_nodes=set(),
            last_flush=time.monotonic(),
        )

        self._streams[vid] = stream

        root = self._traversal.root_id(vid)
        stream.node_depth[root] = -1
        stream.published_nodes.add(root)

        event = self._emitter.begin(vid)
        await session.emit(event)

    # ---------------------------------------------------------

    async def finish_view(
        self,
        session: Session,
        view: View,
        *,
        override: OutputStreaming | None = None,
    ) -> None:

        vid = override.id if override and override.id else view.id
        assert vid is not None

        stream = self._streams.get(vid)

        if stream is None:
            return

        await self._flush(stream)

        event = self._emitter.finish(vid)
        await session.emit(event)

        self._streams.pop(vid, None)

    # ---------------------------------------------------------

    async def flush_view(self, view_id: str) -> None:

        stream = self._streams.get(view_id)
        if stream is None:
            return

        await self._flush(stream)

    # ---------------------------------------------------------

    async def abort_view(
        self,
        session: Session,
        view_id: str,
    ) -> None:

        stream = self._streams.get(view_id)

        if stream is None:
            return

        stream.event_queue.clear()

        event = self._emitter.finish(view_id)
        await session.emit(event)

        self._streams.pop(view_id, None)

    # ---------------------------------------------------------

    async def emit_block(
        self,
        session: Session,
        *,
        view: View,
        block: Block,
        parent_id: str | None = None,
        suffix: str | int = 0,
        override: OutputStreaming | None = None,
    ) -> None:

        vid = override.id if override and override.id else view.id
        assert vid is not None

        stream = self._streams.get(vid)
        if stream is None:
            return

        block_id = block.id
        if block_id is None:
            raise RuntimeError("Block without id passed to streamer")

        parent = self._traversal.resolve_parent(vid, parent_id)
        parent_depth = stream.node_depth.get(parent, -1)
        depth = parent_depth + 1

        node, children, text_fields = self._traversal.prepare_block(
            block,
            parent=parent,
            depth=depth,
        )

        stream.node_depth[node.id] = depth

        stream.event_queue.append(PatchAppendStructure(nodes=[node]))

        # children
        for i, child in enumerate(children):
            await self.emit_block(
                session,
                view=view,
                block=child,
                parent_id=block_id,
                suffix=i,
                override=override,
            )

        # textfields
        for key, value in text_fields:
            if isinstance(value, str) and value:

                min_size = max(self.MIN_CHUNK_SIZE, int(self.MAX_CHUNK_SIZE * 0.2))

                for chunk in iter_chunks(value, min_size, self.MAX_CHUNK_SIZE):

                    stream.event_queue.append(
                        PatchAppendText(
                            block_id=block_id,
                            key=key,
                            text=chunk,
                        )
                    )

        stream.event_queue.append(
            PatchFinishNode(
                block_id=block_id,
            )
        )

        await self._maybe_flush(stream)

    # ---------------------------------------------------------

    async def _maybe_flush(self, stream: _ViewStream) -> None:

        now = time.monotonic()

        if len(stream.event_queue) >= self.BATCH_SIZE:
            await self._flush(stream)
            return

        if now - stream.last_flush >= stream.interval:
            await self._flush(stream)

    # ---------------------------------------------------------

    async def _flush(self, stream: _ViewStream) -> None:

        if not stream.event_queue:
            return

        if stream.view_id not in self._streams:
            return

        ops = []
        remaining = []

        for op in stream.event_queue:

            if isinstance(op, PatchAppendStructure):

                node = op.nodes[0]

                if node.parent not in stream.published_nodes:
                    remaining.append(op)
                    continue

                stream.published_nodes.add(node.id)
                ops.append(op)
                continue

            if isinstance(op, PatchAppendText):

                if op.block_id not in stream.published_nodes:
                    remaining.append(op)
                    continue

                ops.append(op)
                continue

            if isinstance(op, PatchFinishNode):

                if op.block_id not in stream.published_nodes:
                    remaining.append(op)
                    continue

                ops.append(op)
                continue

        stream.event_queue = remaining

        if not ops:
            return

        ops = ops[: self.BATCH_SIZE]

        event = self._emitter.emit(stream.view_id, ops)
        await stream.session.emit(event)

        stream.last_flush = time.monotonic()

    # ---------------------------------------------------------

    def _effective(
        self,
        policy: OutputStreamPolicy,
        override: OutputStreaming | None,
    ) -> EffectiveStreaming:

        if override is None:
            enabled = bool(policy.enabled)
            interval = float(policy.interval)
            chunk_size = int(policy.chunk_tokens)
            sid = None
        else:
            enabled = bool(policy.enabled) and bool(override.enabled)
            interval = (
                override.interval if override.interval is not None else policy.interval
            )
            chunk_size = (
                override.chunk_tokens
                if override.chunk_tokens is not None
                else policy.chunk_tokens
            )
            sid = override.id

        interval = max(self.MIN_INTERVAL, min(self.MAX_INTERVAL, interval))
        chunk_size = max(self.MIN_CHUNK_SIZE, min(self.MAX_CHUNK_SIZE, chunk_size))

        return EffectiveStreaming(
            enabled=enabled,
            id=sid,
            interval=interval,
            chunk_size=chunk_size,
            jitter=0.0,
            punctuation_pause=0.0,
        )
