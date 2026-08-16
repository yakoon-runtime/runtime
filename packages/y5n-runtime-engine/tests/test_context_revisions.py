"""Phase 1 E2E — a real engine flow writes context onto revisions (ADR-17).

The engine establishes the invocation ABI before every step
(``CommandEngine._next_step``). A command running as a real flow therefore
writes entities whose revisions carry the full context envelope: actor,
session, command, trace. Three writes from one command share one trace.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from y5n.runtime.api.flow.primitives import EmitView, Pulse, Stop
from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.store.event.backends.memory import MemoryBackend
from y5n.runtime.store.event.store import create_entity_store

NS = Namespace("test", "widget")


async def _load_revision_contexts(store, entity_ids):
    contexts = []
    for eid in entity_ids:
        revs = await store.on_load_revisions(
            domain_id=NS.domain,
            kind_id=NS.kind,
            space_id=NS.space,
            entity_id=eid,
            rev_gt=0,
            ts_lte=datetime.now(UTC),
        )
        contexts.append(revs[-1].context)
    return contexts


@pytest.mark.asyncio
async def test_flow_writes_carry_full_context(harness):
    """A command (flow) writing 3 entities stamps actor/session/command/trace."""

    store = create_entity_store(MemoryBackend())

    async def main():
        for eid in ("e1", "e2", "e3"):
            await store.append(
                key=NS.get_key(eid),
                patch=[{"op": "add", "path": "/name", "value": eid}],
            )
        yield Pulse(effects=[EmitView(view={"kind": "text", "text": "ok"})])
        yield Pulse()

    # Prepare the session so the invocation carries identity + cwd.
    harness.session.set_identity(
        Key.from_parts("users", "user", "global", "u-1"), "stefan"
    )
    harness.session.set_cwd("/opt/worlds")
    harness.session.set_data("fs:root", "/workspace")

    flow = await harness.start(main)
    pulse = await harness.run_until_stop(flow)
    assert isinstance(pulse.control, Stop)

    contexts = await _load_revision_contexts(store, ("e1", "e2", "e3"))

    assert contexts[0] == contexts[1] == contexts[2]
    ctx = contexts[0]
    assert ctx is not None
    assert ctx["actor"] == {"id": "users/user/global#u-1", "name": "stefan"}
    assert ctx["session"]["key"] == "test/session/runtime#test-1"
    assert ctx["session"]["security_context"] == "normal"
    assert ctx["command"]["path"] == "/test"
    assert ctx["command"]["flow_id"] == flow.id
    assert ctx["command"]["args"] == []
