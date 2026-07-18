from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from y5n.base.document.transfer import (
    DocumentEvent,
    Node,
    PatchAppendStructure,
    PatchFinishNode,
    PatchOp,
)
from y5n.base.runtime import InputContext
from y5n.runtime.runtime import Session


class EventDispatcher:

    BATCH_SIZE = 128
    MAX_BUFFER_DELAY = 0.05

    def __init__(
        self,
        on_create_begin_event: OnCreateBeginEvent,
        on_create_batch_event: OnCreateEmitEvent,
        on_create_finish_event: OnCreateFinishEvent,
        on_get_traversal_root: OnGetTraversalRoot,
        on_get_traversal_parent: OnGetTraversalParent,
        on_get_traversal_prepare: OnGetTraversalPrepareBlock,
    ) -> None:
        self.on_create_begin_event = on_create_begin_event
        self.on_create_batch_event = on_create_batch_event
        self.on_create_finish_event = on_create_finish_event

        self.on_get_traversal_root = on_get_traversal_root
        self.on_get_traversal_parent = on_get_traversal_parent
        self.on_get_traversal_prepare = on_get_traversal_prepare

        self._streams: dict[str, _ViewStream] = {}

    # ---------------------------------------------------------
    # LIFECYCLE
    # ---------------------------------------------------------

    async def begin_projection(
        self,
        session: Session,
        document: dict,
        *,
        ctx: InputContext | None,
        job_id: str,
        reset: bool = True,
        view_params: dict | None = None,
    ) -> None:

        vid = document.get("id")
        if not vid:
            raise RuntimeError("Document without id")

        header = document.get("header")
        if header is None:
            raise RuntimeError("document.header cannot be None")

        stream = _ViewStream(
            session=session,
            projection_id=vid,
            ctx=ctx,
            job_id=job_id,
            view_params=view_params,
            event_queue=[],
            node_depth={},
            published_nodes=set(),
            last_flush=time.monotonic(),
        )

        self._streams[vid] = stream

        root = self.on_get_traversal_root(
            projection_id=vid,
        )

        stream.node_depth[root] = -1
        stream.published_nodes.add(root)

        if reset:
            await session.emit(
                self.on_create_begin_event(
                    header=header,
                    ctx=ctx,
                    vid=vid,
                    job_id=stream.job_id,
                    view_params=view_params,
                )
            )

    # ---------------------------------------------------------

    async def finish_projection(
        self,
        session: Session,
        document: dict,
    ) -> None:

        vid = document.get("id")
        if not vid:
            raise RuntimeError("Document without id")

        stream = self._streams.get(vid)
        if stream is None:
            return

        await self._flush(stream)

        await session.emit(
            self.on_create_finish_event(
                vid=vid,
                ctx=stream.ctx,
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
            self.on_create_finish_event(
                vid=projection_id,
                ctx=stream.ctx,
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
        document: dict,
    ) -> None:

        vid = document.get("id")
        if not vid:
            raise RuntimeError("Document without id")

        for block in document.get("blocks", []):
            await self.emit_block(
                session,
                document=document,
                block=block,
            )

    # ---------------------------------------------------------
    # CORE EMIT
    # ---------------------------------------------------------

    async def emit_block(
        self,
        session: Session,
        *,
        document: dict,
        block: dict,
        parent_id: str | None = None,
    ) -> None:

        vid = document.get("id")
        if not vid:
            raise RuntimeError("Document without id")

        stream = self._streams.get(vid)
        if stream is None:
            return

        block_id = block.get("id")
        if block_id is None:
            raise RuntimeError("Block without id passed to dispatcher")

        parent = self.on_get_traversal_parent(projection_id=vid, parent_id=parent_id)
        parent_depth = stream.node_depth.get(parent, -1)
        depth = parent_depth + 1

        node, children = self.on_get_traversal_prepare(
            block=block,
            parent=parent,
            depth=depth,
        )

        stream.node_depth[node.id] = depth

        # -------------------------------------------------
        # STRUCTURE
        # -------------------------------------------------
        stream.event_queue.append(
            PatchAppendStructure(nodes=[node]),
        )

        # -------------------------------------------------
        # CHILDREN
        # -------------------------------------------------
        for child in children:

            await self.emit_block(
                session,
                document=document,
                block=child,
                parent_id=node.id,
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
            self.on_create_batch_event(
                vid=stream.projection_id,
                ctx=stream.ctx,
                ops=ops,
                job_id=stream.job_id,
            )
        )

        stream.last_flush = time.monotonic()


# ---------------------------------------------------------
# INTERNAL STREAM STATE
# ---------------------------------------------------------


@dataclass
class _ViewStream:
    session: Session
    projection_id: str
    ctx: InputContext | None
    job_id: str
    event_queue: list
    node_depth: dict[str, int]
    published_nodes: set[str]
    last_flush: float
    view_params: dict | None = None


# -------------
# --- PORTS ---
# -------------


class OnCreateBeginEvent(Protocol):
    def __call__(
        self,
        *,
        header: dict,
        vid: str,
        ctx: InputContext | None,
        job_id: str,
        view_params: dict | None = None,
    ) -> DocumentEvent: ...


class OnCreateEmitEvent(Protocol):
    def __call__(
        self,
        *,
        vid: str,
        ops: list[PatchOp],
        job_id: str,
        ctx: InputContext | None,
    ) -> DocumentEvent: ...


class OnCreateFinishEvent(Protocol):
    def __call__(
        self,
        *,
        vid: str,
        job_id: str,
        ctx: InputContext | None,
    ) -> DocumentEvent: ...


class OnGetTraversalRoot(Protocol):
    def __call__(self, *, projection_id: str) -> str: ...


class OnGetTraversalParent(Protocol):
    def __call__(self, *, projection_id: str, parent_id: str | None) -> str: ...


class OnGetTraversalPrepareBlock(Protocol):
    def __call__(
        self, *, block: dict, parent: str, depth: int
    ) -> tuple[Node, list[dict]]: ...
