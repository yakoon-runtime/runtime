"""Store resolution (ADR-18, Phase 2): the runtime derives the physical store
from the calling node's declared profile.

Chain: ``call.caller_path`` → ``tree.find()`` → ``node.store`` → registry →
the physical store. ``sdk.store()`` stays parameterless; the resolution lives
in the runtime, not in the SDK.
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


def _call(caller_path: str) -> Call:
    return Call(
        port="store",
        method="",
        caller_path=caller_path,
        caller_session_key="test/session/runtime#s-1",
    )


def _key(domain: str, kind: str, space: str, entity_id: str) -> dict:
    return {
        "namespace": {"domain": domain, "kind": kind, "space": space},
        "id": entity_id,
    }


def _tree_with_declared_store(tmp_path: Path) -> Tree:
    _write(
        tmp_path / "crm" / "contact" / "add" / ".yak" / "yak.yml",
        "\n".join(
            [
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:x:run",
                "store: crm",
            ]
        ),
    )
    _write(
        tmp_path / "usr" / "bin" / "pwd" / ".yak" / "yak.yml",
        "\n".join(
            [
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:x:run",
            ]
        ),
    )
    return _build_tree(tmp_path)


def test_resolver_binds_declared_profile_to_registered_store(tmp_path: Path):
    tree = _tree_with_declared_store(tmp_path)
    crm_store = create_entity_store(MemoryBackend())
    default_store = create_entity_store(MemoryBackend())

    resolver = StoreResolver(
        tree=tree,
        stores={"crm": crm_store},
        default=default_store,
    )

    assert resolver.resolve(_call("/crm/contact/add")) is crm_store
    assert resolver.resolve(_call("/usr/bin/pwd")) is default_store


def test_resolver_falls_back_when_profile_not_registered(tmp_path: Path):
    tree = _tree_with_declared_store(tmp_path)
    default_store = create_entity_store(MemoryBackend())

    resolver = StoreResolver(tree=tree, default=default_store)

    assert resolver.resolve(_call("/crm/contact/add")) is default_store


@pytest.mark.asyncio
async def test_adapter_writes_land_in_the_resolved_store(tmp_path: Path):
    tree = _tree_with_declared_store(tmp_path)
    crm_store = create_entity_store(MemoryBackend())
    default_store = create_entity_store(MemoryBackend())
    seq = Sequencer(ShardAllocator(MemoryShardRepository()))

    adapter = StoreAdapter(
        default_store,
        seq,
        resolver=StoreResolver(
            tree=tree, stores={"crm": crm_store}, default=default_store
        ),
    )

    crm_key = _key("crm", "contact", "global", "1")
    other_key = _key("crm", "contact", "global", "2")

    await adapter.replace(_call("/crm/contact/add"), key=crm_key, doc={"name": "ada"})
    await adapter.replace(_call("/usr/bin/pwd"), key=other_key, doc={"name": "grace"})

    crm_ns = Namespace("crm", "contact", "global")
    other_ns = Namespace("crm", "contact", "global")

    assert (await crm_store.get(key=Key(namespace=crm_ns, id="1"))).data == {
        "name": "ada"
    }
    assert (await default_store.get(key=Key(namespace=other_ns, id="2"))).data == {
        "name": "grace"
    }
