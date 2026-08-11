"""Store resolution (ADR-18/19): the runtime resolves the physical store.

Two steps: ``call.caller_path`` → the node's declared stores (which pack am
I?), then ``call.store_name`` → which store do I want (or the first
declared store). The registry maps logical names to ``StoreRuntime``
instances. There is no default store: a node without a declared store
resolves to None.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.nodes.tree import Tree
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


def _key(domain: str, kind: str, space: str, entity_id: str) -> _KeyDict:
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
    crm_rt = _runtime()

    resolver = StoreResolver(tree=tree, stores={"crm": crm_rt})

    assert resolver.resolve(_call("/crm/contact/add")) is crm_rt
    assert resolver.resolve(_call("/usr/bin/pwd")) is None


def test_resolver_raises_on_multiple_stores_without_name(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)
    crm_rt = _runtime()
    telemetry_rt = _runtime()

    resolver = StoreResolver(
        tree=tree,
        stores={"crm": crm_rt, "telemetry": telemetry_rt},
    )

    with pytest.raises(ValueError, match="Multiple stores declared"):
        resolver.resolve(_call("/crm/sync"))


def test_resolver_binds_named_store(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)
    crm_rt = _runtime()
    telemetry_rt = _runtime()

    resolver = StoreResolver(
        tree=tree,
        stores={"crm": crm_rt, "telemetry": telemetry_rt},
    )

    assert resolver.resolve(_call("/crm/sync", store_name="telemetry")) is telemetry_rt
    assert resolver.resolve(_call("/crm/sync", store_name="crm")) is crm_rt


def test_resolver_declared_but_unregistered_is_none(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)

    resolver = StoreResolver(tree=tree)

    assert resolver.resolve(_call("/crm/contact/add")) is None
    assert resolver.resolve(_call("/crm/sync", store_name="telemetry")) is None


@pytest.mark.asyncio
async def test_adapter_writes_land_in_the_resolved_store(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)
    crm_rt = _runtime()
    telemetry_rt = _runtime()

    adapter = StoreAdapter(
        resolver=StoreResolver(
            tree=tree,
            stores={"crm": crm_rt, "telemetry": telemetry_rt},
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

    # No default store: a node without declared stores cannot write.
    with pytest.raises(RuntimeError, match="No store bound"):
        await adapter.replace(
            _call("/usr/bin/pwd"), key=other_key, doc={"name": "grace"}
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


def test_resolver_raises_on_undeclared_named_store(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)

    resolver = StoreResolver(tree=tree)

    with pytest.raises(ValueError, match="Undeclared store 'nope'"):
        resolver.resolve(_call("/crm/contact/add", store_name="nope"))


def test_resolver_allows_any_declared_store_even_unregistered(tmp_path: Path):
    tree = _tree_with_declared_stores(tmp_path)

    resolver = StoreResolver(tree=tree)

    # telemetry is declared by /crm/sync but has no physical store yet —
    # it resolves to None until the installation provides it (no default).
    assert resolver.resolve(_call("/crm/sync", store_name="telemetry")) is None
