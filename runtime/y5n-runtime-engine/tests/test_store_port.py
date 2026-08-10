"""Store port (ADR-17): the shared Event Store over the Runtime Bus.

The SDK calls ``store.get/replace/record/...`` via the ``store`` port; the
wire adapter maps RPC-safe structured keys (dicts) onto the EntityStore.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.wire.adapter.store import StoreAdapter, _KeyDict
from y5n.runtime.store.event.backends.memory import MemoryBackend
from y5n.runtime.store.event.store import create_entity_store
from y5n.runtime.store.sequence.allocator import ShardAllocator
from y5n.runtime.store.sequence.backends.memory import MemoryShardRepository
from y5n.runtime.store.sequence.runtime import Sequencer


def _adapter() -> StoreAdapter:
    store = create_entity_store(MemoryBackend())
    seq = Sequencer(ShardAllocator(MemoryShardRepository()))
    return StoreAdapter(store, seq)


def _call(port="store") -> Call:
    return Call(
        port=port,
        method="",
        caller_path="/usr/bin/ls",
        caller_session_key="test/session/runtime#s-1",
    )


def _key(domain: str, kind: str, space: str, entity_id: str) -> _KeyDict:
    return {
        "namespace": {"domain": domain, "kind": kind, "space": space},
        "id": entity_id,
    }


@pytest.mark.asyncio
async def test_replace_and_get_roundtrip():
    adapter = _adapter()
    key = _key("luma", "box", "global", "1")

    result = await adapter.replace(_call(), key=key, doc={"name": "office"})
    assert result["rev"] == 1

    got = await adapter.get(_call(), key=key)
    assert got["data"] == {"name": "office"}
    assert got["rev"] == 1


@pytest.mark.asyncio
async def test_record_is_write_only():
    adapter = _adapter()
    key = _key("system", "activity", "global", "evt-1")

    result = await adapter.record(
        _call(), key=key, doc={"kind": "read", "path": "/opt"}
    )
    assert result["rev"] == 1
    assert result["snapshot_written"] is False

    got = await adapter.get(_call(), key=key)
    assert got["data"] is None


@pytest.mark.asyncio
async def test_history_returns_revisions_with_context():
    adapter = _adapter()
    key = _key("system", "activity", "global", "evt-1")

    await adapter.record(_call(), key=key, doc={"kind": "read", "path": "/opt"})

    history = await adapter.history(_call(), key=key)
    assert len(history) == 1
    assert history[0]["rev"] == 1
    assert history[0]["data"] == {"kind": "read", "path": "/opt"}
    assert history[0]["ts"] is not None


@pytest.mark.asyncio
async def test_append_and_next_id():
    adapter = _adapter()
    key = _key("crm", "contact", "global", "1")

    result = await adapter.append(
        _call(), key=key, patch=[{"op": "add", "path": "/x", "value": 1}]
    )
    assert result["rev"] == 1

    next_id = await adapter.next_id(_call(), prefix="c")
    assert isinstance(next_id, str)
