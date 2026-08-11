"""Phase 3 (ADR-18/19): the runtime materializes every store from the
installation through its StoreFactory.

The runtime knows no backend schemes. The installation binds each logical
store — including the runtime's own `runtime` store — to a factory import
path and an opaque config. A node without a declared store resolves to
None: there is no default store.
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


def _deployment(extra: str = "", *, runtime: str = "") -> str:
    runtime_entry = (
        "  runtime:\n"
        "    factory: y5n.runtime.store.event.wire:EventStoreFactory\n"
        "    config:\n"
        "      backend: memory\n"
        if runtime == "memory"
        else ""
    )
    return "stores:\n" + runtime_entry + extra


FACTORY = "y5n.runtime.store.event.wire:EventStoreFactory"


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


def test_registry_instantiates_class_factories(monkeypatch):
    """ADR-19: a factory path names a class — the registry instantiates it
    before calling ``build(config)``. The config must reach the build.

    Regression: calling ``Class.build(config)`` without instantiating
    binds ``config`` as ``self`` and silently builds with ``config=None``.
    """
    from y5n.runtime.engine import installation as inst_mod
    from y5n.runtime.store.event.backends.memory import MemoryBackend
    from y5n.runtime.store.event.runtime import StoreRuntime
    from y5n.runtime.store.event.store import create_entity_store

    received: list = []

    class _RecordingFactory:
        def build(self, config):
            received.append(config)
            return StoreRuntime(objects=create_entity_store(MemoryBackend()))

    monkeypatch.setattr(inst_mod, "load_store_factory", lambda path: _RecordingFactory)

    installation = inst_mod.Installation(
        stores={
            "crm": inst_mod.StoreBinding(
                store="crm",
                factory="x",
                config={"backend": "postgres", "dsn": "env://CRM_DB"},
            ),
        },
    )

    registry = inst_mod.build_store_registry(installation)

    assert received == [{"backend": "postgres", "dsn": "env://CRM_DB"}]
    assert "crm" in registry


def test_two_logical_stores_share_one_factory_target():
    """ADR-19: stores with the same factory and config share one instance."""
    from y5n.runtime.engine.installation import (
        Installation,
        StoreBinding,
        build_store_registry,
    )
    from y5n.runtime.store.event.runtime import StoreRuntime

    installation = Installation(
        stores={
            "crm": StoreBinding(
                store="crm", factory=FACTORY, config={"backend": "memory"}
            ),
            "ident": StoreBinding(
                store="ident", factory=FACTORY, config={"backend": "memory"}
            ),
        },
    )

    registry = build_store_registry(installation)
    second = build_store_registry(installation)

    assert registry["crm"] is registry["ident"]
    assert isinstance(registry["crm"], StoreRuntime)
    assert registry["crm"] is not second["crm"]


def test_load_installation_roundtrip(tmp_path: Path):
    """The deployment file materialized by yak is consumed by the engine."""
    from y5n.runtime.engine.installation import load_installation, to_dict

    deployment_file = tmp_path / "deployment.yml"
    deployment_file.write_text(
        "stores:\n"
        "  crm:\n"
        f"    factory: {FACTORY}\n"
        "    config:\n"
        "      backend: memory\n"
    )

    installation = load_installation(deployment_file)
    assert installation is not None
    binding = installation.binding_for("crm")
    assert binding is not None
    assert binding.factory == FACTORY
    assert binding.config == {"backend": "memory"}

    data = to_dict(installation)
    assert data["stores"]["crm"]["factory"] == FACTORY
    assert data["stores"]["crm"]["config"] == {"backend": "memory"}


@pytest.mark.asyncio
async def test_runtime_consumes_a_real_deployment_file(tmp_path: Path):
    """ADR-19: the runtime builds its registry from the deployment file.

    The full chain: a real `deployment.yml` on disk → `build_runtime`
    consumes it → the resolver serves the configured store, and a node
    without a declared store resolves to None — there is no default.
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
    _write(
        tmp_path / "usr" / "bin" / "pwd" / ".yak" / "yak.yml",
        "host: /boot/python/runtime\n",
    )

    # The deployment file the assembler would have written.
    deployment_file = tmp_path / ".yak" / "installation" / "deployment.yml"
    deployment_file.parent.mkdir(parents=True, exist_ok=True)
    deployment_file.write_text(
        _deployment(
            "  crm:\n"
            f"    factory: {FACTORY}\n"
            "    config:\n"
            "      backend: memory\n",
            runtime="memory",
        )
    )

    from y5n.runtime.api.runtime.bus import _make_default_bus, get_bus, set_bus
    from y5n.runtime.engine.settings import RuntimeSettings, Settings
    from y5n.runtime.engine.wire.adapter.store import StoreAdapter
    from y5n.runtime.engine.wire.runtime import build_runtime

    previous = get_bus()
    bus = _make_default_bus()
    set_bus(bus)

    try:
        settings = Settings(
            runtime=RuntimeSettings(
                workspace_path=str(tmp_path),
                installation_path=str(deployment_file),
            ),
        )
        manager = build_runtime(settings=settings)
        await manager.setup()

        adapter = None
        for candidate in get_bus().transport._adapters.values():
            if isinstance(candidate, StoreAdapter):
                adapter = candidate
                break
        assert adapter is not None

        crm_resolved = adapter._resolver.resolve("crm")
        assert crm_resolved is not None
        assert crm_resolved.sequencer is not None

        # The runtime store is bound; an unbound name resolves to None.
        assert adapter._resolver.resolve("ident") is None
    finally:
        set_bus(previous)


def test_runtime_raises_without_installation(tmp_path: Path):
    """ADR-19: no runtime without an installation."""
    import os

    os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

    from y5n.runtime.api.runtime.bus import _make_default_bus, get_bus, set_bus
    from y5n.runtime.engine.settings import RuntimeSettings, Settings
    from y5n.runtime.engine.wire.runtime import build_runtime

    previous = get_bus()
    bus = _make_default_bus()
    set_bus(bus)

    try:
        settings = Settings(
            runtime=RuntimeSettings(
                workspace_path=str(tmp_path),
                installation_path=str(tmp_path / "missing" / "deployment.yml"),
            ),
        )
        with pytest.raises(RuntimeError, match="No installation found"):
            build_runtime(settings=settings)
    finally:
        set_bus(previous)


def test_runtime_raises_without_runtime_store(tmp_path: Path):
    """ADR-19: the runtime requires its own `runtime` store in the installation."""
    import os

    os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

    _write(
        tmp_path / "crm" / ".yak" / "yak.yml",
        "stores:\n  - crm\n",
    )
    _write(
        tmp_path / "crm" / "contact" / "add" / ".yak" / "yak.yml",
        "host: /boot/python/runtime\nentry:\n  run: pack:test:run\n",
    )

    deployment_file = tmp_path / ".yak" / "installation" / "deployment.yml"
    deployment_file.parent.mkdir(parents=True, exist_ok=True)
    deployment_file.write_text(
        _deployment(
            "  crm:\n"
            f"    factory: {FACTORY}\n"
            "    config:\n"
            "      backend: memory\n",
        )
    )

    from y5n.runtime.api.runtime.bus import _make_default_bus, get_bus, set_bus
    from y5n.runtime.engine.settings import RuntimeSettings, Settings
    from y5n.runtime.engine.wire.runtime import build_runtime

    previous = get_bus()
    bus = _make_default_bus()
    set_bus(bus)

    try:
        settings = Settings(
            runtime=RuntimeSettings(
                workspace_path=str(tmp_path),
                installation_path=str(deployment_file),
            ),
        )
        with pytest.raises(RuntimeError, match="binds no 'runtime' store"):
            build_runtime(settings=settings)
    finally:
        set_bus(previous)
