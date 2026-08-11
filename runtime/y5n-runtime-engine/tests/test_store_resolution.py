"""Store resolution (ADR-18/19): the resolver routes a logical name.

The installation binds every declared store to a ``StoreRuntime``. At
runtime the resolver only routes: ``store("crm")`` leads to the crm store
the installation built. There is no per-call node check and no default
store — a name the installation did not bind resolves to None.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.wire.adapter.store import StoreAdapter, StoreResolver, _KeyDict
from y5n.runtime.store.event.backends.memory import MemoryBackend
from y5n.runtime.store.event.runtime import StoreRuntime
from y5n.runtime.store.event.store import create_entity_store
from y5n.runtime.store.sequence.allocator import ShardAllocator
from y5n.runtime.store.sequence.backends.memory import MemoryShardRepository
from y5n.runtime.store.sequence.runtime import Sequencer


def _runtime() -> StoreRuntime:
    store = create_entity_store(MemoryBackend())
    seq = Sequencer(ShardAllocator(MemoryShardRepository()))
    return StoreRuntime(objects=store, sequencer=seq)


def _call(store_name: str | None = None) -> Call:
    return Call(
        port="store",
        method="",
        caller_path="/usr/bin/su",
        caller_session_key="test/session/runtime#s-1",
        store_name=store_name,
    )


def _key(domain: str, kind: str, space: str, entity_id: str) -> _KeyDict:
    return {
        "namespace": {"domain": domain, "kind": kind, "space": space},
        "id": entity_id,
    }


def test_resolver_routes_a_named_store():
    crm_rt = _runtime()
    resolver = StoreResolver(stores={"crm": crm_rt})

    assert resolver.resolve("crm") is crm_rt
    assert resolver.resolve("ident") is None
    assert resolver.resolve(None) is None


def test_resolver_without_registry_resolves_nothing():
    resolver = StoreResolver()
    assert resolver.resolve("crm") is None


@pytest.mark.asyncio
async def test_adapter_writes_land_in_the_routed_store():
    crm_rt = _runtime()
    telemetry_rt = _runtime()

    adapter = StoreAdapter(
        resolver=StoreResolver(stores={"crm": crm_rt, "telemetry": telemetry_rt}),
    )

    await adapter.replace(
        _call("crm"), key=_key("crm", "contact", "global", "1"), doc={"name": "ada"}
    )
    await adapter.replace(
        _call("telemetry"),
        key=_key("telemetry", "event", "global", "2"),
        doc={"kind": "event"},
    )

    assert (
        await crm_rt.objects.get(
            key=Key(namespace=Namespace("crm", "contact", "global"), id="1")
        )
    ).data == {"name": "ada"}
    assert (
        await telemetry_rt.objects.get(
            key=Key(namespace=Namespace("telemetry", "event", "global"), id="2")
        )
    ).data == {"kind": "event"}


@pytest.mark.asyncio
async def test_adapter_raises_for_uninstalled_store():
    adapter = StoreAdapter(resolver=StoreResolver(stores={}))

    with pytest.raises(RuntimeError, match="not installed"):
        await adapter.replace(
            _call("crm"), key=_key("crm", "contact", "global", "1"), doc={}
        )


@pytest.mark.asyncio
async def test_adapter_raises_without_store_name():
    adapter = StoreAdapter(resolver=StoreResolver(stores={"crm": _runtime()}))

    with pytest.raises(RuntimeError, match="No store specified"):
        await adapter.replace(
            _call(), key=_key("crm", "contact", "global", "1"), doc={}
        )


@pytest.mark.asyncio
async def test_next_id_uses_the_routed_stores_sequencer():
    crm_rt = _runtime()
    adapter = StoreAdapter(resolver=StoreResolver(stores={"crm": crm_rt}))

    next_id = await adapter.next_id(_call("crm"), prefix="c")
    assert isinstance(next_id, str)
