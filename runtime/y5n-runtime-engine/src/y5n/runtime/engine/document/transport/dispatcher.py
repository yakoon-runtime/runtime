from __future__ import annotations

import time
from dataclasses import dataclass

from y5n.runtime.api.document.transfer import PatchAppendStructure, PatchFinishNode
from y5n.runtime.api.runtime import InputContext
from y5n.runtime.engine.runtime import Session

from .factory import EventFactory
from .traversal import EventTraversal


class EventDispatcher:

    BATCH_SIZE = 128
    MAX_BUFFER_DELAY = 0.05

    def __init__(
        self,
        factory: EventFactory,
        traversal: EventTraversal,
    ) -> None:
        self.factory = factory
        self.traversal = traversal
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
            event_queue=[],
            node_depth={},
            last_flush=time.monotonic(),
        )

        self._streams[vid] = stream

        root = self.traversal.root_id(projection_id=vid)
        stream.node_depth[root] = -1

        if reset:
            await session.emit(
                self.factory.begin_event(
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
            self.factory.finish_event(
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
            self.factory.finish_event(
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
                document=document,
                block=block,
            )

    # ---------------------------------------------------------
    # CORE EMIT — iterative traversal
    # ---------------------------------------------------------

    async def emit_block(
        self,
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

        if block.get("id") is None:
            raise RuntimeError("Block without id passed to dispatcher")

        # Iterative depth-first traversal. A node's structure op is queued
        # before its children's, so the client always receives the tree
        # topology first; the remaining content flows in size- and
        # time-bounded chunks (BATCH_SIZE / MAX_BUFFER_DELAY).
        stack: list[tuple[dict, str | None] | _Finish] = [(block, parent_id)]

        while stack:
            item = stack.pop()

            if isinstance(item, _Finish):
                stream.event_queue.append(PatchFinishNode(block_id=item.node_id))
                await self._maybe_flush(stream)
                continue

            cur_block, cur_parent = item

            parent = self.traversal.resolve_parent(
                projection_id=vid,
                parent_id=cur_parent,
            )
            depth = stream.node_depth.get(parent, -1) + 1

            node, children = self.traversal.prepare_block(
                cur_block,
                parent=parent,
                depth=depth,
            )

            stream.node_depth[node["id"]] = depth

            stream.event_queue.append(PatchAppendStructure(nodes=[node]))

            stack.append(_Finish(node["id"]))
            for child in reversed(children):
                stack.append((child, node["id"]))

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

        ops, tail = (
            stream.event_queue[: self.BATCH_SIZE],
            stream.event_queue[self.BATCH_SIZE :],
        )

        stream.event_queue = tail

        if not ops:
            return

        await stream.session.emit(
            self.factory.patch_event(
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
    last_flush: float


@dataclass(frozen=True)
class _Finish:
    node_id: str
