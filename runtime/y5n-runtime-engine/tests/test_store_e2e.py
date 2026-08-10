"""End-to-end (ADR-18): a pack declares its stores once, commands inherit.

The full chain:

    Pack root (stores: [crm])
        │
        ▼
    Parser → Node.stores
        │
        ▼
    Tree (BuildState inherits pack-level stores to commands)
        │
        ▼
    StoreCollector → {crm, luma, ident}
        │
        ▼
    StoreResolver → sdk.store("crm") / sdk.store()
"""

from __future__ import annotations

from pathlib import Path

import pytest
from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.api.runtime.context import set_context
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.services.store_collector import StoreCollector
from y5n.runtime.engine.wire.adapter.store import StoreResolver, _KeyDict
from y5n.runtime.store.event.backends.memory import MemoryBackend
from y5n.runtime.store.event.store import create_entity_store


def _build_tree(root: Path) -> Tree:
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=root, executors=registry)
    tree.build()
    return tree


def _pack(root: Path, name: str, store: str) -> None:
    (root / name / ".yak").mkdir(parents=True, exist_ok=True)
    (root / name / ".yak" / "yak.yml").write_text(f"stores:\n  - {store}\n")


def _command(root: Path, *parts: str) -> None:
    p = root.joinpath(*parts)
    (p / ".yak").mkdir(parents=True, exist_ok=True)
    (p / ".yak" / "yak.yml").write_text("host: /boot/python/runtime\n")


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


def test_commands_inherit_the_pack_store(tmp_path: Path):
    _pack(tmp_path, "crm", "crm")
    _command(tmp_path, "crm", "contact", "add")

    tree = _build_tree(tmp_path)

    add = tree.find("/crm/contact/add")
    assert add is not None
    assert add.stores == ["crm"]


def test_full_chain_declares_and_resolves(tmp_path: Path):
    _pack(tmp_path, "crm", "crm")
    _pack(tmp_path, "luma", "luma")
    _pack(tmp_path, "ident", "ident")
    _command(tmp_path, "crm", "contact", "add")
    _command(tmp_path, "crm", "sync")
    _command(tmp_path, "luma", "box", "add")

    tree = _build_tree(tmp_path)

    # 1. The tree describes the installed packs.
    assert StoreCollector(tree).collect() == ["crm", "ident", "luma"]

    # 2. The resolver binds a named store.
    crm_store = create_entity_store(MemoryBackend())
    luma_store = create_entity_store(MemoryBackend())
    default_store = create_entity_store(MemoryBackend())
    resolver = StoreResolver(
        tree=tree,
        stores={"crm": crm_store, "luma": luma_store},
        default=default_store,
    )

    assert resolver.resolve(_call("/crm/contact/add")) is crm_store
    assert resolver.resolve(_call("/crm/contact/add", store_name="crm")) is crm_store
    assert resolver.resolve(_call("/luma/box/add")) is luma_store

    # 3. An undeclared store name resolves to the default.
    assert (
        resolver.resolve(_call("/crm/contact/add", store_name="nope")) is default_store
    )


@pytest.mark.asyncio
async def test_sdk_store_resolves_the_declared_store(tmp_path: Path):
    from y5n.sdk import store

    _pack(tmp_path, "crm", "crm")
    _command(tmp_path, "crm", "contact", "add")

    set_context({"node": {"path": "/crm/contact/add", "stores": ["crm"]}})
    try:
        client = store()
        assert client._name == "crm"
        named = store("crm")
        assert named._name == "crm"
    finally:
        set_context({})


@pytest.mark.asyncio
async def test_sdk_store_raises_with_multiple_declared(tmp_path: Path):
    from y5n.sdk import store

    _pack(tmp_path, "crm", "crm")
    _pack(tmp_path, "crm2", "telemetry")
    _command(tmp_path, "crm", "sync")

    set_context({"node": {"path": "/crm/sync", "stores": ["crm", "telemetry"]}})
    try:
        with pytest.raises(ValueError, match="Multiple stores declared"):
            store()
    finally:
        set_context({})


@pytest.mark.asyncio
async def test_writes_land_in_the_declared_store(tmp_path: Path):
    from y5n.runtime.api.naming import Key, Namespace
    from y5n.runtime.api.runtime.bus import _make_default_bus, get_bus, set_bus
    from y5n.runtime.engine.wire.adapter.store import StoreAdapter
    from y5n.runtime.store.sequence.allocator import ShardAllocator
    from y5n.runtime.store.sequence.backends.memory import MemoryShardRepository
    from y5n.runtime.store.sequence.runtime import Sequencer

    _pack(tmp_path, "crm", "crm")
    _command(tmp_path, "crm", "contact", "add")

    crm_store = create_entity_store(MemoryBackend())
    default_store = create_entity_store(MemoryBackend())
    seq = Sequencer(ShardAllocator(MemoryShardRepository()))

    previous = get_bus()
    bus = _make_default_bus()
    set_bus(bus)
    try:
        adapter = StoreAdapter(
            default_store,
            seq,
            resolver=StoreResolver(
                tree=_build_tree(tmp_path),
                stores={"crm": crm_store},
                default=default_store,
            ),
        )
        key = _key("crm", "contact", "global", "1")
        await adapter.replace(_call("/crm/contact/add"), key=key, doc={"name": "ada"})

        assert (
            await crm_store.get(
                key=Key(namespace=Namespace("crm", "contact", "global"), id="1")
            )
        ).data == {"name": "ada"}
        assert (
            await default_store.get(
                key=Key(namespace=Namespace("crm", "contact", "global"), id="1")
            )
        ).data is None
    finally:
        set_bus(previous)
