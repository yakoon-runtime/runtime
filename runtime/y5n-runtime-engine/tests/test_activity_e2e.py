"""Phase 2 E2E — a completed flow emits command.executed (ADR-17).

The scheduler's ``on_flow_complete`` hook fires when a flow stops; the
wire connects it to the activity observer. A command running as a real
flow therefore appends a ``command.executed`` activity event — write-only,
with the full context envelope.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from y5n.runtime.api.flow.primitives import Pulse
from y5n.runtime.engine.services.activity import ActivityService, activity_namespace
from y5n.runtime.store.event.backends.memory import MemoryBackend
from y5n.runtime.store.event.store import create_entity_store


def _activity_revisions(backend: MemoryBackend):
    """Return (key, RevisionRow) for every revision in the activity namespace."""
    ns = activity_namespace()
    out = []
    for (domain, kind, space, _eid), rows in backend._revisions.items():
        if (domain, kind, space) == (ns.domain, ns.kind, ns.space):
            out.extend((eid, row) for row in rows for eid in [row.entity_id])
    return out


@pytest.mark.asyncio
async def test_flow_complete_emits_command_executed(harness):
    """A real flow end → command.executed lands in the store, write-only."""

    backend = MemoryBackend()
    store = create_entity_store(backend)
    service = ActivityService(on_record=store.record)

    async def on_flow_complete(flow, session):
        await service.record(
            kind="command.executed",
            session=session,
            payload={"path": str(flow.node.path) if flow.node else None},
        )

    async def main():
        yield Pulse()
        yield Pulse()

    harness.scheduler.on_flow_complete = on_flow_complete

    flow = await harness.start(main)
    await harness.run_until_stop(flow)

    entries = _activity_revisions(backend)
    assert len(entries) == 1
    entity_id, rev = entries[0]

    # Write-only: the activity entity has a revision but no current state.
    ns = activity_namespace()
    cur = await store.on_load_current(
        domain_id=ns.domain, kind_id=ns.kind, space_id=ns.space, entity_id=entity_id
    )
    assert cur is None

    # The payload records the command; context is ambient from the flow.
    assert rev.patch[0]["value"]["kind"] == "command.executed"
    assert rev.patch[0]["value"]["payload"]["path"] == "/test"
    assert rev.context["session"]["key"] == "test/session/runtime#test-1"


@pytest.mark.asyncio
async def test_flow_complete_activity_has_actor_context(harness):
    """The activity event written from a completed flow carries the actor."""

    backend = MemoryBackend()
    store = create_entity_store(backend)
    service = ActivityService(on_record=store.record)

    async def on_flow_complete(flow, session):
        await service.record(kind="command.executed", session=session)

    async def main():
        yield Pulse()

    harness.session.set_identity(
        __import__("y5n.runtime.api.naming", fromlist=["Key"]).Key.from_parts(
            "users", "user", "global", "u-1"
        ),
        "stefan",
    )
    harness.scheduler.on_flow_complete = on_flow_complete

    flow = await harness.start(main)
    await harness.run_until_stop(flow)

    entries = _activity_revisions(backend)
    assert len(entries) == 1
    _, rev = entries[0]
    assert rev.context["actor"] == {
        "id": "users/user/global#u-1",
        "name": "stefan",
    }
