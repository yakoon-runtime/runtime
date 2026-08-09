"""Phase 3 (ADR-18): the deployment configures store bindings.

The runtime config's ``stores:`` section declares logical store names; the
engine turns them into physical stores and feeds the resolver's registry.
A pack declaring ``store: crm`` resolves to the *configured* crm store, not
to the default.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from y5n.runtime.api.runtime.bus import _make_default_bus, get_bus, set_bus
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.settings import RuntimeSettings, Settings
from y5n.runtime.engine.wire.adapter.store import StoreAdapter
from y5n.runtime.engine.wire.runtime import build_runtime
from y5n.runtime.store.event.settings import StorageSettings


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


@pytest.mark.asyncio
async def test_configured_store_binding_reaches_the_resolver(
    tmp_path: Path, monkeypatch
):
    import os

    os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

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

    previous = get_bus()
    bus = _make_default_bus()
    set_bus(bus)

    try:
        settings = Settings(
            runtime=RuntimeSettings(workspace_path=str(tmp_path)),
            storage=StorageSettings(backend="memory", dsn=""),
            stores={
                "crm": StorageSettings(backend="memory", dsn=""),
            },
        )
        manager = build_runtime(settings=settings)
        await manager.setup()

        adapter = None
        for candidate in get_bus().transport._adapters.values():
            if isinstance(candidate, StoreAdapter):
                adapter = candidate
                break
        assert adapter is not None

        crm_resolved = adapter._resolver.resolve(
            Call(port="store", method="", caller_path="/crm/contact/add")
        )
        default_resolved = adapter._resolver.resolve(
            Call(port="store", method="", caller_path="/usr/bin/pwd")
        )

        assert crm_resolved is not None
        assert default_resolved is not None
        assert crm_resolved is not default_resolved
    finally:
        set_bus(previous)
