from __future__ import annotations

import time
from dataclasses import dataclass

from yakoon.base.projection.model import Block, Projection
from yakoon.base.projection.transport import (
    PatchAppendStructure,
    PatchAppendText,
    PatchFinishNode,
)
from yakoon.platform.projection import ViewEmitter, ViewTraversal
from yakoon.platform.runtime import Session

# ---------------------------------------------------------
# HARD transport limit (NOT UX!)
# ---------------------------------------------------------
MAX_TEXT_PAYLOAD = 4096


def split_payload(text: str, max_size: int):
    for i in range(0, len(text), max_size):
        yield text[i : i + max_size]


# ---------------------------------------------------------
# INTERNAL STREAM STATE
# ---------------------------------------------------------
@dataclass
class _ViewStream:
    session: Session
    projection_id: str
    job_id: str

    event_queue: list

    node_depth: dict[str, int]
    published_nodes: set[str]

    last_flush: float


# ---------------------------------------------------------
# DISPATCHER
# ---------------------------------------------------------
class EventProjectionDispatcher:

    BATCH_SIZE = 64
    MAX_BUFFER_DELAY = 0.05  # technical flush

    def __init__(self) -> None:
        self._streams: dict[str, _ViewStream] = {}
        self._traversal = ViewTraversal()
        self._emitter = ViewEmitter()

    # ---------------------------------------------------------
    # LIFECYCLE
    # ---------------------------------------------------------

    async def begin_projection(
        self,
        session: Session,
        projection: Projection,
        *,
        job_id: str,
    ) -> None:

        vid = projection.id
        assert vid is not None

        if projection.header is None:
            raise RuntimeError("projection.header cannot be None")

        stream = _ViewStream(
            session=session,
            projection_id=vid,
            job_id=job_id,
            event_queue=[],
            node_depth={},
            published_nodes=set(),
            last_flush=time.monotonic(),
        )

        self._streams[vid] = stream

        root = self._traversal.root_id(vid)
        stream.node_depth[root] = -1
        stream.published_nodes.add(root)

        await session.emit(
            self._emitter.begin(
                header=projection.header,
                vid=vid,
                job_id=stream.job_id,
            )
        )

    # ---------------------------------------------------------

    async def finish_projection(
        self,
        session: Session,
        projection: Projection,
    ) -> None:

        vid = projection.id
        assert vid is not None

        stream = self._streams.get(vid)
        if stream is None:
            return

        await self._flush(stream)

        await session.emit(
            self._emitter.finish(
                vid=vid,
                job_id=stream.job_id,
            )
        )

        self._streams.pop(vid, None)

    # ---------------------------------------------------------

    async def abort_projection(
        self,
        session: Session,
        projection_id: str,
    ) -> None:

        stream = self._streams.get(projection_id)
        if stream is None:
            return

        stream.event_queue.clear()

        await session.emit(
            self._emitter.finish(
                vid=projection_id,
                job_id=stream.job_id,
            )
        )

        self._streams.pop(projection_id, None)

    # ---------------------------------------------------------
    # ENTRY
    # ---------------------------------------------------------

    async def emit_projection(
        self,
        session: Session,
        projection: Projection,
    ) -> None:
        """
        Emit full projection (block-aware).
        """

        vid = projection.id
        assert vid is not None

        for block in projection.blocks:
            await self.emit_block(
                session,
                projection=projection,
                block=block,
            )

    # ---------------------------------------------------------
    # CORE EMIT
    # ---------------------------------------------------------

    async def emit_block(
        self,
        session: Session,
        *,
        projection: Projection,
        block: Block,
        parent_id: str | None = None,
    ) -> None:

        vid = projection.id
        assert vid is not None

        stream = self._streams.get(vid)
        if stream is None:
            return

        if block.id is None:
            raise RuntimeError("Block without id passed to dispatcher")

        parent = self._traversal.resolve_parent(vid, parent_id)
        parent_depth = stream.node_depth.get(parent, -1)
        depth = parent_depth + 1

        node, children, text_fields = self._traversal.prepare_block(
            block,
            parent=parent,
            depth=depth,
        )

        stream.node_depth[node.id] = depth

        # -------------------------------------------------
        # STRUCTURE
        # -------------------------------------------------
        stream.event_queue.append(PatchAppendStructure(nodes=[node]))

        # -------------------------------------------------
        # CHILDREN
        # -------------------------------------------------
        for child in children:

            await self.emit_block(
                session,
                projection=projection,
                block=child,
                parent_id=node.id,
            )

        # -------------------------------------------------
        # TEXT
        # -------------------------------------------------
        for key, value in text_fields:
            if not value:
                continue

            if len(value) <= MAX_TEXT_PAYLOAD:
                stream.event_queue.append(
                    PatchAppendText(
                        block_id=node.id,
                        key=key,
                        text=value,
                    )
                )
            else:
                for chunk in split_payload(value, MAX_TEXT_PAYLOAD):
                    stream.event_queue.append(
                        PatchAppendText(
                            block_id=node.id,
                            key=key,
                            text=chunk,
                        )
                    )

        # -------------------------------------------------
        # FINISH
        # -------------------------------------------------
        stream.event_queue.append(PatchFinishNode(block_id=node.id))

        await self._maybe_flush(stream)

    # ---------------------------------------------------------
    # BUFFER / FLUSH
    # ---------------------------------------------------------

    async def _maybe_flush(self, stream: _ViewStream) -> None:

        now = time.monotonic()

        if len(stream.event_queue) >= self.BATCH_SIZE:
            await self._flush(stream)
            return

        if now - stream.last_flush >= self.MAX_BUFFER_DELAY:
            await self._flush(stream)

    # ---------------------------------------------------------

    async def _flush(self, stream: _ViewStream) -> None:

        if not stream.event_queue:
            return

        if stream.projection_id not in self._streams:
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

        await stream.session.emit(
            self._emitter.emit(
                vid=stream.projection_id,
                ops=ops,
                job_id=stream.job_id,
            )
        )

        stream.last_flush = time.monotonic()
