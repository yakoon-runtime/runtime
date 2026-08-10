"""Phase 3 (ADR-18): the runtime collects the store names from the packs.

The runtime knows the logical store names the installed packs declare
(``store: crm`` → the name ``crm``) — nothing more. What each name means
(backend, instance) is deployment knowledge, assembled later by ``yak``.
The tree only *describes* the components; a collector evaluates them.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.services.store_collector import StoreCollector


def _build_tree(root: Path) -> Tree:
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=root, executors=registry)
    tree.build()
    return tree


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _make_call(caller_path: str, store_name: str | None = None):
    from y5n.runtime.api.runtime.invoke import Call

    return Call(
        port="store",
        method="",
        caller_path=caller_path,
        caller_session_key="test/session/runtime#s-1",
        store_name=store_name,
    )


def test_collector_gets_declared_store_names(tmp_path: Path):
    _write(
        tmp_path / "crm" / "contact" / "add" / ".yak" / "yak.yml",
        "stores: [crm]\n",
    )
    _write(
        tmp_path / "ident" / "grant" / ".yak" / "yak.yml",
        "stores: [security]\n",
    )
    _write(
        tmp_path / "luma" / "box" / ".yak" / "yak.yml",
        "stores: [luma]\n",
    )
    _write(
        tmp_path / "usr" / "bin" / "pwd" / ".yak" / "yak.yml",
        "host: /boot/python/runtime\n",
    )

    tree = _build_tree(tmp_path)

    assert StoreCollector(tree).collect() == ["crm", "luma", "security"]


def test_collector_names_without_duplicates(tmp_path: Path):
    _write(
        tmp_path / "crm" / "contact" / "add" / ".yak" / "yak.yml",
        "stores: [crm]\n",
    )
    _write(
        tmp_path / "crm" / "contact" / "edit" / ".yak" / "yak.yml",
        "stores: [crm]\n",
    )

    tree = _build_tree(tmp_path)

    assert StoreCollector(tree).collect() == ["crm"]


def test_collector_without_stores_is_empty(tmp_path: Path):
    _write(
        tmp_path / "usr" / "bin" / "pwd" / ".yak" / "yak.yml",
        "host: /boot/python/runtime\n",
    )

    tree = _build_tree(tmp_path)

    assert StoreCollector(tree).collect() == []


def test_two_logical_stores_share_one_physical_deployment():
    """ADR-19: several logical stores on one deployment share one instance."""
    from y5n.runtime.engine.installation import (
        Deployment,
        Installation,
        StoreMapping,
        build_store_registry,
    )
    from y5n.runtime.store.event.backends.memory import MemoryBackend
    from y5n.runtime.store.event.store import create_entity_store

    installation = Installation(
        stores={
            "crm": StoreMapping(store="crm", deployment="postgres-main"),
            "ident": StoreMapping(store="ident", deployment="postgres-main"),
        },
        deployments={
            "postgres-main": Deployment(name="postgres-main", backend="memory"),
        },
    )
    default_objects = create_entity_store(MemoryBackend())

    registry = build_store_registry(
        installation,
        default_objects,
        lambda dep: create_entity_store(MemoryBackend()),
    )

    assert registry["crm"] is registry["ident"]
    assert registry["crm"] is not default_objects


def test_unmapped_store_resolves_to_default():
    """ADR-19: a store without a deployment entry uses the default."""
    from y5n.runtime.engine.installation import (
        Installation,
        StoreMapping,
        build_store_registry,
    )
    from y5n.runtime.store.event.backends.memory import MemoryBackend
    from y5n.runtime.store.event.store import create_entity_store

    installation = Installation(
        stores={
            "crm": StoreMapping(store="crm", deployment="postgres-main"),
        },
        deployments={},
    )
    default_objects = create_entity_store(MemoryBackend())

    registry = build_store_registry(
        installation,
        default_objects,
        lambda dep: create_entity_store(MemoryBackend()),
    )

    assert registry["crm"] is default_objects


def test_load_installation_roundtrip(tmp_path: Path):
    """The deployment file materialized by yak is consumed by the engine."""
    from y5n.runtime.engine.installation import load_installation, to_dict

    deployment_file = tmp_path / "deployment.yml"
    deployment_file.write_text(
        "stores:\n"
        "  crm:\n"
        "    deployment: postgres-main\n"
        "deployments:\n"
        "  postgres-main:\n"
        "    backend: memory\n"
    )

    installation = load_installation(deployment_file)
    assert installation is not None
    deployment = installation.deployment_for("crm")
    assert deployment is not None
    assert deployment.backend == "memory"

    data = to_dict(installation)
    assert data["stores"]["crm"]["deployment"] == "postgres-main"


@pytest.mark.asyncio
async def test_runtime_consumes_a_real_deployment_file(tmp_path: Path):
    """ADR-19: the runtime builds its registry from the deployment file.

    The full chain: a real `deployment.yml` on disk → `build_runtime`
    consumes it → the resolver serves the configured store.
    """
    import os

    os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

    # A minimal tree: one pack declaring a store, one command.
    _write(
        tmp_path / "crm" / ".yak" / "yak.yml",
        "stores:\n  - crm\n",
    )
    _write(
        tmp_path / "crm" / "contact" / "add" / ".yak" / "yak.yml",
        "host: /boot/python/runtime\nentry:\n  run: pack:test:run\n",
    )

    # The deployment file the assembler would have written.
    deployment_file = tmp_path / ".yak" / "installation" / "deployment.yml"
    deployment_file.parent.mkdir(parents=True, exist_ok=True)
    deployment_file.write_text(
        "stores:\n"
        "  crm:\n"
        "    deployment: crm-main\n"
        "deployments:\n"
        "  crm-main:\n"
        "    backend: memory\n"
    )

    from y5n.runtime.api.runtime.bus import _make_default_bus, get_bus, set_bus
    from y5n.runtime.engine.settings import RuntimeSettings, Settings
    from y5n.runtime.engine.wire.adapter.store import StoreAdapter
    from y5n.runtime.engine.wire.runtime import build_runtime
    from y5n.runtime.store.event.settings import StorageSettings

    previous = get_bus()
    bus = _make_default_bus()
    set_bus(bus)

    try:
        settings = Settings(
            runtime=RuntimeSettings(
                workspace_path=str(tmp_path),
                installation_path=str(deployment_file),
            ),
            storage=StorageSettings(backend="memory", dsn=""),
        )
        manager = build_runtime(settings=settings)
        await manager.setup()

        adapter = None
        for candidate in get_bus().transport._adapters.values():
            if isinstance(candidate, StoreAdapter):
                adapter = candidate
                break
        assert adapter is not None

        crm_resolved = adapter._resolver.resolve(_make_call("/crm/contact/add", "crm"))
        assert crm_resolved is not None
        assert crm_resolved is not adapter._resolver._default
    finally:
        set_bus(previous)
