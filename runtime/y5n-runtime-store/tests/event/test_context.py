"""Phase 1 — Context on every revision (ADR-17).

Every write inside a command carries the ambient invocation context:
actor, session, command, trace. Three writes from one command must share
the same context envelope (trace correlation).
"""

from __future__ import annotations

from datetime import UTC, datetime

from y5n.runtime.api.naming import Namespace
from y5n.runtime.api.runtime.context import Context, set_context
from y5n.runtime.store.event.backends.memory import MemoryBackend
from y5n.runtime.store.event.store import create_entity_store

NS = Namespace("test", "widget")


def build_store():
    return create_entity_store(MemoryBackend())


def _invocation(flow_id: str) -> dict:
    return {
        "node": {"path": "/usr/bin/create", "name": "create"},
        "cwd": "/",
        "workspace": "/w",
        "user": {"id": "u1", "name": "stefan"},
        "session": {"key": "s1", "security_context": "normal"},
        "flow": {"id": flow_id, "key": "create"},
        "args": ["--world", "crm"],
    }


def _load_revisions(store, entity_id):
    return store.on_load_revisions(
        domain_id=NS.domain,
        kind_id=NS.kind,
        space_id=NS.space,
        entity_id=entity_id,
        rev_gt=0,
        ts_lte=datetime.now(UTC),
    )


async def test_write_without_context_stores_none():
    store = build_store()
    await store.append(
        key=NS.get_key("e1"), patch=[{"op": "add", "path": "/name", "value": "one"}]
    )

    revs = await _load_revisions(store, "e1")
    assert len(revs) == 1
    assert revs[0].context is None


async def test_write_inside_command_carries_full_context():
    store = build_store()
    set_context(_invocation(flow_id="f1"))

    await store.append(
        key=NS.get_key("e1"), patch=[{"op": "add", "path": "/name", "value": "one"}]
    )

    revs = await _load_revisions(store, "e1")
    ctx = revs[0].context
    assert ctx is not None
    assert ctx["actor"] == {"id": "u1", "name": "stefan"}
    assert ctx["session"] == {"key": "s1", "security_context": "normal"}
    assert ctx["command"] == {
        "path": "/usr/bin/create",
        "flow_id": "f1",
        "args": ["--world", "crm"],
    }


async def test_one_command_three_entities_share_trace():
    store = build_store()
    set_context(_invocation(flow_id="f42"))

    for eid in ("e1", "e2", "e3"):
        await store.append(
            key=NS.get_key(eid), patch=[{"op": "add", "path": "/name", "value": eid}]
        )

    contexts = []
    for eid in ("e1", "e2", "e3"):
        revs = await _load_revisions(store, eid)
        contexts.append(revs[0].context)

    assert contexts[0] == contexts[1] == contexts[2]
    assert contexts[0]["command"]["flow_id"] == "f42"
    assert contexts[0]["actor"] == {"id": "u1", "name": "stefan"}


async def test_context_value_object_projects_and_serializes():
    ctx = Context.from_invocation(_invocation(flow_id="f9"))

    assert ctx.actor.id == "u1"
    assert ctx.actor.name == "stefan"
    assert ctx.session.key == "s1"
    assert ctx.session.security_context == "normal"
    assert ctx.command.path == "/usr/bin/create"
    assert ctx.command.flow_id == "f9"
    assert ctx.command.args == ("--world", "crm")

    d = ctx.to_dict()
    assert d["actor"] == {"id": "u1", "name": "stefan"}
    assert d["session"] == {"key": "s1", "security_context": "normal"}
    assert d["command"] == {
        "path": "/usr/bin/create",
        "flow_id": "f9",
        "args": ["--world", "crm"],
    }


async def test_record_never_materializes_current_state():
    store = build_store()
    key = NS.get_key("evt-1")

    result = await store.record(key=key, doc={"kind": "read", "path": "/opt"})

    assert result.rev == 1
    assert result.snapshot_written is False

    cur = await store.on_load_current(
        domain_id=NS.domain, kind_id=NS.kind, space_id=NS.space, entity_id="evt-1"
    )
    assert cur is None


async def test_record_carries_ambient_context():
    store = build_store()
    set_context(_invocation(flow_id="f-activity"))

    await store.record(key=NS.get_key("evt-1"), doc={"kind": "read", "path": "/opt"})

    revs = await _load_revisions(store, "evt-1")
    ctx = revs[0].context
    assert ctx is not None
    assert ctx["actor"] == {"id": "u1", "name": "stefan"}
    assert ctx["command"]["flow_id"] == "f-activity"


async def test_record_explicit_context_overrides_ambient():
    store = build_store()
    set_context(_invocation(flow_id="f-ambient"))

    await store.record(
        key=NS.get_key("evt-1"),
        doc={"kind": "permission.denied", "path": "/usr/bin/ls"},
        context={"actor": {"id": "u-99", "name": "system"}, "session": {}},
    )

    revs = await _load_revisions(store, "evt-1")
    ctx = revs[0].context
    assert ctx is not None
    assert ctx["actor"] == {"id": "u-99", "name": "system"}
    assert "command" not in ctx
