"""Phase 2 — Activity events (ADR-17).

An activity event records what a session did or was refused, without
changing state. It is appended write-only (never materialized as current)
and carries the actor/session context.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from y5n.runtime.api.naming import Key
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData
from y5n.runtime.engine.services.activity import ActivityService, activity_namespace
from y5n.runtime.store.event.backends.memory import MemoryBackend
from y5n.runtime.store.event.store import create_entity_store


def _session() -> Session:
    session = Session(
        key=Key.from_parts("system", "activity", "global", "s-1"),
        data=SessionData(),
    )
    session.set_identity(Key.from_parts("users", "user", "global", "u-1"), "stefan")
    session.set_security_context("normal")
    return session


async def _load_activity(store, entity_id):
    ns = activity_namespace()
    revs = await store.on_load_revisions(
        domain_id=ns.domain,
        kind_id=ns.kind,
        space_id=ns.space,
        entity_id=entity_id,
        rev_gt=0,
        ts_lte=datetime.now(UTC),
    )
    return revs


@pytest.mark.asyncio
async def test_record_never_materializes_current_state():
    store = create_entity_store(MemoryBackend())
    ns = activity_namespace()
    key = ns.get_key("evt-1")

    await store.record(key=key, doc={"kind": "read", "path": "/opt"})

    cur = await store.on_load_current(
        domain_id=ns.domain, kind_id=ns.kind, space_id=ns.space, entity_id="evt-1"
    )
    assert cur is None

    revs = await _load_activity(store, "evt-1")
    assert len(revs) == 1
    assert revs[0].patch[0]["value"] == {"kind": "read", "path": "/opt"}


@pytest.mark.asyncio
async def test_record_forwards_kind_payload_and_context():
    writes: list[dict] = []

    async def on_record(*, key, doc, expected_rev=None, context=None):
        writes.append({"key": key, "doc": doc, "context": context})

    service = ActivityService(on_record=on_record)
    session = _session()

    await service.record(
        kind="permission.denied",
        session=session,
        payload={"path": "/usr/bin/ls", "operation": "execute"},
    )

    assert len(writes) == 1
    entry = writes[0]
    assert entry["key"].namespace == activity_namespace()
    assert entry["doc"] == {
        "kind": "permission.denied",
        "payload": {"path": "/usr/bin/ls", "operation": "execute"},
    }
    assert entry["context"]["actor"] == {
        "id": "users/user/global#u-1",
        "name": "stefan",
    }
    assert entry["context"]["session"]["key"] == "system/activity/global#s-1"
    assert entry["context"]["session"]["security_context"] == "normal"


@pytest.mark.asyncio
async def test_record_without_session_has_no_context():
    writes: list[dict] = []

    async def on_record(*, key, doc, expected_rev=None, context=None):
        writes.append({"key": key, "doc": doc, "context": context})

    service = ActivityService(on_record=on_record)

    await service.record(kind="read", session=None)

    assert len(writes) == 1
    assert writes[0]["context"] is None
