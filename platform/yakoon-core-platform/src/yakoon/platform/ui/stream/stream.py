from __future__ import annotations

import random
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass

from yakoon.base.runtime import Session
from yakoon.base.ui import (
    Block,
    EffectiveStreaming,
    NodeSpec,
    OutputStreaming,
    OutputStreamPolicy,
    PatchAppendStructure,
    PatchAppendText,
    PatchReset,
    PatchSpec,
    ViewEvent,
    ViewSpec,
)

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
    structure_queue: list[NodeSpec]
    text_queue: list[PatchAppendText]
    published_nodes: set[str]
    last_flush: float


class DefaultOutputStreamService:

    MIN_INTERVAL = 0.05
    MAX_INTERVAL = 0.25

    MIN_CHUNK_SIZE = 8
    MAX_CHUNK_SIZE = 96

    STRUCT_NODE_BATCH = 128
    TEXT_BATCH = 32

    DEFAULT_JITTER = 0.10
    DEFAULT_PUNCT_PAUSE = 1.25
    FLUSH_INTERVAL = 1.0 / 30.0

    def __init__(self) -> None:
        self._streams: dict[str, _ViewStream] = {}

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
        view: ViewSpec,
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
            structure_queue=[],
            text_queue=[],
            published_nodes=set(),
            last_flush=time.monotonic(),
        )

        self._streams[vid] = stream

        await session.emit(
            ViewEvent(
                id=vid,
                patch=PatchSpec(ops=[PatchReset()], final=False),
            )
        )

    # ---------------------------------------------------------

    async def finish_view(
        self,
        session: Session,
        view: ViewSpec,
        *,
        override: OutputStreaming | None = None,
    ) -> None:

        vid = override.id if override and override.id else view.id
        assert vid is not None

        stream = self._streams.get(vid)

        if stream is None:
            return

        await self._flush(stream)

        await session.emit(
            ViewEvent(
                id=vid,
                patch=PatchSpec(ops=[], final=True),
            )
        )

        self._streams.pop(vid, None)

    # ---------------------------------------------------------

    async def emit_block(
        self,
        session: Session,
        *,
        view: ViewSpec,
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

        parent = parent_id or f"{vid}:root"

        node = NodeSpec.from_block(block, parent=parent)
        stream.structure_queue.append(node)

        text = getattr(block, "text", None)
        if isinstance(text, str) and text:
            min_size = max(self.MIN_CHUNK_SIZE, int(self.MAX_CHUNK_SIZE * 0.4))
            for chunk in iter_chunks(text, min_size, self.MAX_CHUNK_SIZE):

                stream.text_queue.append(
                    PatchAppendText(
                        block_id=block_id,
                        key="text",
                        text=chunk,
                    )
                )

                if chunk.rstrip().endswith((".", "!", "?", ":", "...")):
                    stream.last_flush -= self.DEFAULT_PUNCT_PAUSE

        await self._maybe_flush(stream)

    # ---------------------------------------------------------

    async def _maybe_flush(self, stream: _ViewStream) -> None:

        now = time.monotonic()

        if len(stream.structure_queue) >= self.STRUCT_NODE_BATCH:
            await self._flush(stream)
            return

        if len(stream.text_queue) >= self.TEXT_BATCH:
            await self._flush(stream)
            return

        jitter = random.uniform(-self.DEFAULT_JITTER, self.DEFAULT_JITTER)
        if now - stream.last_flush >= max(self.MIN_INTERVAL, stream.interval + jitter):
            await self._flush(stream)

    # ---------------------------------------------------------

    async def _flush(self, stream: _ViewStream) -> None:

        ops = []

        # -------------------------------------------------
        # STEP 1: ensure structure exists for pending text
        # -------------------------------------------------

        if stream.text_queue:
            first_text = stream.text_queue[0]
            if first_text.block_id not in stream.published_nodes:
                if not stream.structure_queue:
                    return

                nodes = stream.structure_queue[: self.STRUCT_NODE_BATCH]
                stream.structure_queue = stream.structure_queue[
                    self.STRUCT_NODE_BATCH :
                ]

                ops.append(PatchAppendStructure(nodes=nodes))
                for n in nodes:
                    stream.published_nodes.add(n.id)

        # -------------------------------------------------
        # STEP 2: send additional structure if queued
        # -------------------------------------------------

        elif stream.structure_queue:
            nodes = stream.structure_queue[: self.STRUCT_NODE_BATCH]
            stream.structure_queue = stream.structure_queue[self.STRUCT_NODE_BATCH :]
            ops.append(PatchAppendStructure(nodes=nodes))
            for n in nodes:
                stream.published_nodes.add(n.id)

        # -------------------------------------------------
        # STEP 3: send text only for known nodes
        # -------------------------------------------------

        safe_text = []
        remaining = []

        for op in stream.text_queue:
            if op.block_id in stream.published_nodes:
                safe_text.append(op)
            else:
                remaining.append(op)
        if safe_text:
            ops.extend(safe_text)
        stream.text_queue = remaining

        if not ops:
            return

        await stream.session.emit(
            ViewEvent(
                id=stream.view_id,
                patch=PatchSpec(ops=ops, final=False),
            )
        )

        stream.last_flush = time.monotonic()

    def _effective(
        self,
        policy: OutputStreamPolicy,
        override: OutputStreaming | None,
    ) -> EffectiveStreaming:

        def _clamp(v: float, lo: float, hi: float) -> float:
            return max(lo, min(hi, v))

        def _clamp_int(v: int, lo: int, hi: int) -> int:
            return max(lo, min(hi, v))

        if override is None:
            enabled = bool(policy.enabled)
            interval = float(policy.interval)
            chunk_size = int(policy.chunk_tokens)
            sid = None
        else:
            enabled = bool(policy.enabled) and bool(override.enabled)
            interval = float(
                override.interval if override.interval is not None else policy.interval
            )
            chunk_size = int(
                override.chunk_tokens
                if override.chunk_tokens is not None
                else policy.chunk_tokens
            )
            sid = override.id

        interval = _clamp(interval, self.MIN_INTERVAL, self.MAX_INTERVAL)
        chunk_size = _clamp_int(chunk_size, self.MIN_CHUNK_SIZE, self.MAX_CHUNK_SIZE)

        return EffectiveStreaming(
            enabled=enabled,
            id=sid,
            interval=interval,
            chunk_size=chunk_size,
            jitter=self.DEFAULT_JITTER,
            punctuation_pause=self.DEFAULT_PUNCT_PAUSE,
        )
