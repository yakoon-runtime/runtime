"""The installation's startup declaration (ADR-25): data contract and
loading only.

`.yak/startup.yml` declares the Session Startup Sequence. These tests
prove the loading contract — absent/empty declarations, order
preservation, tolerant validation — and that the loaded sequence is
carried on the runtime manager. Nothing executes the sequence here.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from y5n.runtime.engine.startup import load_startup

FACTORY = "y5n.runtime.store.event.wire:EventStoreFactory"


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def test_absent_file_declares_no_startup(tmp_path: Path):
    assert load_startup(tmp_path / "startup.yml") == ()


def test_empty_file_declares_no_startup(tmp_path: Path):
    assert load_startup(_write(tmp_path / "startup.yml", "")) == ()


def test_missing_key_declares_no_startup(tmp_path: Path):
    assert load_startup(_write(tmp_path / "startup.yml", "other: x\n")) == ()


def test_empty_sequence_declares_no_startup(tmp_path: Path):
    assert load_startup(_write(tmp_path / "startup.yml", "startup: []\n")) == ()


def test_single_command_preserved_exactly(tmp_path: Path):
    file = _write(tmp_path / "startup.yml", "startup:\n  - welcome\n")
    assert load_startup(file) == ("welcome",)


def test_multiple_commands_preserve_declaration_order(tmp_path: Path):
    file = _write(
        tmp_path / "startup.yml",
        "startup:\n  - welcome\n  - mem\n  - /system/status\n",
    )
    assert load_startup(file) == ("welcome", "mem", "/system/status")


def test_non_sequence_value_declares_no_startup(tmp_path: Path):
    file = _write(tmp_path / "startup.yml", "startup: welcome\n")
    assert load_startup(file) == ()


def test_non_mapping_document_declares_no_startup(tmp_path: Path):
    file = _write(tmp_path / "startup.yml", "- welcome\n")
    assert load_startup(file) == ()


def test_invalid_items_are_skipped(tmp_path: Path):
    file = _write(
        tmp_path / "startup.yml",
        "startup:\n  - welcome\n  - ''\n  - 3\n  - mem\n",
    )
    assert load_startup(file) == ("welcome", "mem")


@pytest.mark.asyncio
async def test_build_runtime_exposes_the_declared_startup(tmp_path: Path):
    """The startup file is installation data: loaded at boot and carried
    on the manager. Nothing executes it here."""
    import os

    os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

    _write(
        tmp_path / "structure" / "usr" / "bin" / "pwd" / ".yak" / "yak.yml",
        "host: /boot/python/runtime\n",
    )
    _write(
        tmp_path / "deployment.yml",
        "stores:\n"
        "  runtime:\n"
        f"    factory: {FACTORY}\n"
        "    config:\n"
        "      backend: memory\n",
    )
    _write(tmp_path / "startup.yml", "startup:\n  - welcome\n  - mem\n")

    from y5n.runtime.api.runtime.bus import _make_default_bus, get_bus, set_bus
    from y5n.runtime.engine.settings import RuntimeSettings, Settings
    from y5n.runtime.engine.wire.runtime import build_runtime

    previous = get_bus()
    set_bus(_make_default_bus())

    try:
        settings = Settings(
            runtime=RuntimeSettings(workspace_path=str(tmp_path / "structure")),
        )
        manager = build_runtime(settings=settings)
        await manager.setup()

        assert manager.startup == ("welcome", "mem")
    finally:
        set_bus(previous)


@pytest.mark.asyncio
async def test_build_runtime_without_startup_file(tmp_path: Path):
    """An installation without a startup file declares no startup."""
    import os

    os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

    _write(
        tmp_path / "structure" / "usr" / "bin" / "pwd" / ".yak" / "yak.yml",
        "host: /boot/python/runtime\n",
    )
    _write(
        tmp_path / "deployment.yml",
        "stores:\n"
        "  runtime:\n"
        f"    factory: {FACTORY}\n"
        "    config:\n"
        "      backend: memory\n",
    )

    from y5n.runtime.api.runtime.bus import _make_default_bus, get_bus, set_bus
    from y5n.runtime.engine.settings import RuntimeSettings, Settings
    from y5n.runtime.engine.wire.runtime import build_runtime

    previous = get_bus()
    set_bus(_make_default_bus())

    try:
        settings = Settings(
            runtime=RuntimeSettings(workspace_path=str(tmp_path / "structure")),
        )
        manager = build_runtime(settings=settings)
        await manager.setup()

        assert manager.startup == ()
    finally:
        set_bus(previous)
