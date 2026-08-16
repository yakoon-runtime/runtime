"""EventDispatcher round-trip tests.

Covers the event stream produced for a document:
  - begin (reset) -> append_structure/finish_node patches -> finish (final)
  - tree order, parent/depth wiring
  - batch truncation at BATCH_SIZE
  - abort discards buffered ops
"""

from __future__ import annotations

from y5n.runtime.api.document.transfer import (
    PatchAppendStructure,
    PatchFinishNode,
)
from y5n.runtime.api.naming import Key
from y5n.runtime.engine.document.transport import (
    EventDispatcher,
    EventFactory,
    EventTraversal,
)
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData


class RecordingIO:
    def __init__(self) -> None:
        self.events: list = []

    async def view(self, event) -> None:
        self.events.append(event)


def _make_session() -> tuple[Session, RecordingIO]:
    session = Session(
        key=Key.from_parts("test", "session", "dispatcher", "1"),
        data=SessionData(),
    )
    io = RecordingIO()
    session.bind_io(io)
    return session, io


def _make_dispatcher() -> EventDispatcher:
    return EventDispatcher(factory=EventFactory(), traversal=EventTraversal())


def _ops(io: RecordingIO) -> list:
    ops: list = []
    for event in io.events[1:-1]:
        ops.extend(event.patch.ops)
    return ops


def _patch_ops(io: RecordingIO) -> list[list]:
    return [
        event.patch.ops
        for event in io.events
        if event is not io.events[0] and event is not io.events[-1]
    ]


async def _dispatch(
    dispatcher: EventDispatcher,
    session: Session,
    document: dict,
    *,
    job_id: str = "job-1",
) -> None:
    await dispatcher.begin_projection(session, document, ctx=None, job_id=job_id)
    await dispatcher.emit_projection(session, document)
    await dispatcher.finish_projection(session, document)


async def test_begin_and_finish_frame_the_stream():
    session, io = _make_session()
    dispatcher = _make_dispatcher()
    document = {"id": "d1", "header": {"role": "info"}, "blocks": []}

    await _dispatch(dispatcher, session, document)

    events = io.events
    assert len(events) == 2
    assert events[0].patch.has_reset()
    assert not events[0].patch.final
    assert events[-1].patch.final
    assert events[-1].patch.ops == []


async def test_structure_ops_in_tree_order_with_parent_depth():
    session, io = _make_session()
    dispatcher = _make_dispatcher()
    document = {
        "id": "d1",
        "header": {"role": "info"},
        "blocks": [
            {"id": "b1", "type": "paragraph", "text": [{"type": "text", "text": "hi"}]},
            {
                "id": "b2",
                "type": "section",
                "blocks": [
                    {
                        "id": "b2-1",
                        "type": "text",
                        "text": [{"type": "text", "text": "x"}],
                    },
                    {
                        "id": "b2-2",
                        "type": "text",
                        "text": [{"type": "text", "text": "y"}],
                    },
                ],
            },
        ],
    }

    await _dispatch(dispatcher, session, document)

    ops = _ops(io)
    assert [type(op).__name__ for op in ops] == [
        "PatchAppendStructure",
        "PatchFinishNode",
        "PatchAppendStructure",
        "PatchAppendStructure",
        "PatchFinishNode",
        "PatchAppendStructure",
        "PatchFinishNode",
        "PatchFinishNode",
    ]

    nodes = [op.nodes[0] for op in ops if isinstance(op, PatchAppendStructure)]
    assert [n["id"] for n in nodes] == ["b1", "b2", "b2-1", "b2-2"]
    assert [n["parent"] for n in nodes] == ["d1:root", "d1:root", "b2", "b2"]
    assert [n["depth"] for n in nodes] == [0, 0, 1, 1]
    assert nodes[0]["type"] == "paragraph"
    assert nodes[0]["props"] == {"text": [{"type": "text", "text": "hi"}]}

    finishes = [op for op in ops if isinstance(op, PatchFinishNode)]
    assert [op.block_id for op in finishes] == ["b1", "b2-1", "b2-2", "b2"]


async def test_block_without_id_is_rejected():
    session, io = _make_session()
    dispatcher = _make_dispatcher()
    document = {
        "id": "d1",
        "header": {"role": "info"},
        "blocks": [{"type": "text", "text": []}],
    }

    await dispatcher.begin_projection(session, document, ctx=None, job_id="job-1")
    import pytest

    with pytest.raises(RuntimeError, match="without id"):
        await dispatcher.emit_projection(session, document)


async def test_batch_truncation_splits_across_patches():
    session, io = _make_session()
    dispatcher = _make_dispatcher()
    n = 200
    document = {
        "id": "d1",
        "header": {"role": "info"},
        "blocks": [
            {"id": f"b{i}", "type": "text", "text": [{"type": "text", "text": str(i)}]}
            for i in range(n)
        ],
    }

    await _dispatch(dispatcher, session, document)

    events = io.events
    assert events[0].patch.has_reset()
    assert events[-1].patch.final

    patches = _patch_ops(io)
    sizes = [len(p) for p in patches]
    assert all(size <= dispatcher.BATCH_SIZE for size in sizes)
    assert sizes[0] == dispatcher.BATCH_SIZE
    assert sizes[-1] < dispatcher.BATCH_SIZE

    ops = _ops(io)
    nodes = [op.nodes[0] for op in ops if isinstance(op, PatchAppendStructure)]
    assert [n["id"] for n in nodes] == [f"b{i}" for i in range(n)]
    assert all(n["parent"] == "d1:root" for n in nodes)


async def test_abort_discards_buffered_ops():
    session, io = _make_session()
    dispatcher = _make_dispatcher()
    document = {
        "id": "d1",
        "header": {"role": "info"},
        "blocks": [{"id": "b1", "type": "text", "text": []}],
    }

    await dispatcher.begin_projection(session, document, ctx=None, job_id="job-1")
    await dispatcher.emit_projection(session, document)
    await dispatcher.abort_projection(session, "d1")

    events = io.events
    assert len(events) == 2
    assert events[0].patch.has_reset()
    assert events[-1].patch.final
    assert events[-1].patch.ops == []
    assert "d1" not in dispatcher._streams
