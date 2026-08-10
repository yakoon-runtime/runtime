"""Store resolution (ADR-18): the runtime resolves the physical store.

Two steps: ``call.caller_path`` → the node's declared stores (which pack am
I?), then ``call.store_name`` → which store do I want (or the first
declared store). The registry maps logical names to physical stores;
unregistered names fall back to the default.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.wire.adapter.store import StoreAdapter, StoreResolver
from y5n.runtime.store.event.backends.memory import MemoryBackend
from y5n.runtime.store.event.store import create_entity_store
from y5n.runtime.store.sequence.allocator import ShardAllocator
from y5n.runtime.store.sequence.backends.memory import MemoryShardRepository
from y5n.runtime.store.sequence.runtime import Sequencer


def _build_tree(root: Path) -> Tree:
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=root, executors=registry)
    tree.build()
    return tree


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _call(caller_path: str, store_name: str | None = None) -> Call:
    return Call(
        port="store",
        method="",
        caller_path=caller_path,
        caller_session_key="test/session/runtime#s-1",
        store_name=store_name,
    )


def _key(domain: str, kind: str, space: str, entity_id: str) -> dict:
    return {
        "namespace": {"domain": domain, "kind": kind, "space": space},
        "id": entity_id,
    }


def _tree_with_declared_stores(tmp_path: Path) -> Tree:
    _write(
        tmp_path / "crm" / "contact" / "add" / ".yak" / "yak.yml",
        "\n".join(
            [
                "stores:",
                "  - crm",
            ]
        ),
    )
    _write(
        tmp_path / "crm" / "sync" / ".yak" / "yak.yml",
        "\n".join(
            [
                "stores:",
                "  - crm",
                "  - telemetry",
            ]
        ),
    )
    _write(
        tmp_path / "usr" / "bin" / "pwd" / ".yak" / "yak.yml",
        "\n".join(
            [
                "host: /boot/python/runtime",
            ]
        ),
    )
    return _build_tree(tmp_path)


def test_resolver_binds_single_declared_store(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)
    crm_store = create_entity_store(MemoryBackend())
    telemetry_store = create_entity_store(MemoryBackend())
    default_store = create_entity_store(MemoryBackend())

    resolver = StoreResolver(
        tree=tree,
        stores={"crm": crm_store, "telemetry": telemetry_store},
        default=default_store,
    )

    assert resolver.resolve(_call("/crm/contact/add")) is crm_store
    assert resolver.resolve(_call("/usr/bin/pwd")) is default_store


def test_resolver_raises_on_multiple_stores_without_name(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)
    crm_store = create_entity_store(MemoryBackend())
    telemetry_store = create_entity_store(MemoryBackend())
    default_store = create_entity_store(MemoryBackend())

    resolver = StoreResolver(
        tree=tree,
        stores={"crm": crm_store, "telemetry": telemetry_store},
        default=default_store,
    )

    with pytest.raises(ValueError, match="Multiple stores declared"):
        resolver.resolve(_call("/crm/sync"))


def test_resolver_binds_named_store(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)
    crm_store = create_entity_store(MemoryBackend())
    telemetry_store = create_entity_store(MemoryBackend())
    default_store = create_entity_store(MemoryBackend())

    resolver = StoreResolver(
        tree=tree,
        stores={"crm": crm_store, "telemetry": telemetry_store},
        default=default_store,
    )

    assert (
        resolver.resolve(_call("/crm/sync", store_name="telemetry")) is telemetry_store
    )
    assert resolver.resolve(_call("/crm/sync", store_name="crm")) is crm_store


def test_resolver_falls_back_when_not_registered(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)
    default_store = create_entity_store(MemoryBackend())

    resolver = StoreResolver(tree=tree, default=default_store)

    assert resolver.resolve(_call("/crm/contact/add")) is default_store
    assert resolver.resolve(_call("/crm/sync", store_name="telemetry")) is default_store


@pytest.mark.asyncio
async def test_adapter_writes_land_in_the_resolved_store(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)
    crm_store = create_entity_store(MemoryBackend())
    telemetry_store = create_entity_store(MemoryBackend())
    default_store = create_entity_store(MemoryBackend())
    seq = Sequencer(ShardAllocator(MemoryShardRepository()))

    adapter = StoreAdapter(
        default_store,
        seq,
        resolver=StoreResolver(
            tree=tree,
            stores={"crm": crm_store, "telemetry": telemetry_store},
            default=default_store,
        ),
    )

    crm_key = _key("crm", "contact", "global", "1")
    telemetry_key = _key("telemetry", "event", "global", "2")
    other_key = _key("crm", "contact", "global", "3")

    await adapter.replace(
        _call("/crm/sync", store_name="crm"), key=crm_key, doc={"name": "ada"}
    )
    await adapter.replace(
        _call("/crm/sync", store_name="telemetry"),
        key=telemetry_key,
        doc={"kind": "event"},
    )
    await adapter.replace(_call("/usr/bin/pwd"), key=other_key, doc={"name": "grace"})

    assert (
        await crm_store.get(
            key=Key(namespace=Namespace("crm", "contact", "global"), id="1")
        )
    ).data == {"name": "ada"}
    assert (
        await telemetry_store.get(
            key=Key(namespace=Namespace("telemetry", "event", "global"), id="2")
        )
    ).data == {"kind": "event"}
    assert (
        await default_store.get(
            key=Key(namespace=Namespace("crm", "contact", "global"), id="3")
        )
    ).data == {"name": "grace"}
