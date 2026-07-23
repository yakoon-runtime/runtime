from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from y5n.runtime.api.naming import Key

_services: dict[str, Any] = {}


def _publish(name: str, service: Any) -> None:
    _services[name] = service


def _get(name: str) -> Any:
    return _services.get(name)


@pytest.fixture(autouse=True)
def _patch_ports(monkeypatch):
    _services.clear()
    import y5n.apps.luma.setup as luma_setup
    import y5n.sdk.ports as sdk_ports

    monkeypatch.setattr(sdk_ports, "publish", _publish)
    monkeypatch.setattr(sdk_ports, "get", _get)
    import asyncio
    asyncio.run(luma_setup.main())
    yield


@pytest.fixture
def worlds():
    return _get("luma.world.service")


@pytest.fixture
def boxes():
    return _get("luma.box.service")


@pytest.fixture
def exits():
    return _get("luma.exit.service")


@pytest.fixture
def notes():
    return _get("luma.note.service")
