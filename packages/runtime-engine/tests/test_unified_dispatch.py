"""Unified dispatch — Resolver decides WHO, Transport decides HOW.

Black-box proof through the real Bus (Resolver + DirectTransport +
CallHandler): a contextual Runtime provider at root and ordinary pack
providers at scoped paths are selected by resolution alone. The transport
follows the resolved provider_id and never consults call.port.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.runtime.bus import _make_default_bus, get_bus, set_bus
from y5n.runtime.api.runtime.context import set_context
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.api.runtime.messages import Placement, RegisterProvider

from y5n.sdk import ports


@pytest.fixture(autouse=True)
def _endpoint(monkeypatch):
    monkeypatch.setenv("YAK_ENDPOINT", "inprocess://")


@pytest.fixture(autouse=True)
def _bus():
    previous = get_bus()
    set_bus(_make_default_bus())
    set_context({})
    yield get_bus()
    set_context({})
    set_bus(previous)


class _RootStoreAdapter:
    """Contextual provider: receives the full Call (like StoreAdapter)."""

    def __init__(self):
        self.calls = []

    async def get(self, call, *, key):
        self.calls.append(call)
        return {"invoked": "system:store", "key": key}


class _PackStore:
    """Ordinary provider: receives business args only."""

    def __init__(self):
        self.calls = []

    async def get(self, **kwargs):
        self.calls.append(kwargs)
        return {"invoked": "pack-provider", "key": kwargs.get("key")}


def _install_root_contextual_provider(adapter) -> None:
    bus = get_bus()
    bus.resolver.register("system:store", {"store": ["get"]}, path="/")
    bus.transport.register_adapter("system:store", adapter)


def _provide_scoped(service) -> None:
    set_context({"node": {"path": "/contacts/customer"}, "session": {"key": "s-1"}})
    ports.provide("store", service)
    set_context({})


def _register_named_provider(provider_id: str, path: str) -> None:
    async def get(**kwargs):
        return {"invoked": provider_id, "key": kwargs.get("key")}

    get_bus().dispatch(
        RegisterProvider(
            provider_id=provider_id,
            exports={"store": ["get"]},
            service={"get": get},
            placement=Placement.SELF,
            caller_path=path,
        )
    )


async def _call(caller_path: str, key: str = "k-1") -> dict:
    call = Call(
        port="store",
        method="get",
        args={"key": key},
        caller_path=caller_path,
        caller_session_key="s-1",
        store_name="worlds",
    )
    response = await get_bus().async_dispatch(call)
    assert response.error is None, response.error
    return response.result


async def test_root_contextual_provider_answers_without_closer_provider():
    adapter = _RootStoreAdapter()
    _install_root_contextual_provider(adapter)

    assert await _call("/worlds") == {"invoked": "system:store", "key": "k-1"}
    assert await _call("/contacts") == {"invoked": "system:store", "key": "k-1"}
    assert len(adapter.calls) == 2


async def test_scoped_ordinary_provider_shadows_root_contextual_provider():
    adapter = _RootStoreAdapter()
    _install_root_contextual_provider(adapter)
    pack = _PackStore()
    _provide_scoped(pack)

    result = await _call("/contacts/customer/edit")

    assert result == {"invoked": "pack-provider", "key": "k-1"}
    assert pack.calls == [{"key": "k-1"}]
    assert adapter.calls == []


async def test_sibling_scope_still_reaches_root_contextual_provider():
    adapter = _RootStoreAdapter()
    _install_root_contextual_provider(adapter)
    _provide_scoped(_PackStore())

    assert (await _call("/worlds"))["invoked"] == "system:store"
    assert (await _call("/contacts"))["invoked"] == "system:store"
    assert (await _call("/contacts/customer"))["invoked"] == "pack-provider"
    assert (await _call("/contacts/customer/edit"))["invoked"] == "pack-provider"

    assert [c.caller_path for c in adapter.calls] == ["/worlds", "/contacts"]


async def test_contextual_provider_receives_full_call():
    adapter = _RootStoreAdapter()
    _install_root_contextual_provider(adapter)

    await _call("/worlds", key="k-9")

    received = adapter.calls[0]
    assert received.port == "store"
    assert received.method == "get"
    assert received.args == {"key": "k-9"}
    assert received.caller_path == "/worlds"
    assert received.caller_session_key == "s-1"
    assert received.store_name == "worlds"


async def test_ordinary_provider_receives_business_args_only():
    _install_root_contextual_provider(_RootStoreAdapter())
    pack = _PackStore()
    _provide_scoped(pack)

    await _call("/contacts/customer/edit", key="k-2")

    assert pack.calls == [{"key": "k-2"}]


async def test_invoked_provider_always_equals_resolver_selected_provider():
    _install_root_contextual_provider(_RootStoreAdapter())
    _register_named_provider("provider:contacts", "/contacts")
    _register_named_provider("provider:customer", "/contacts/customer")

    probes = {
        "/": "system:store",
        "/worlds": "system:store",
        "/contacts": "provider:contacts",
        "/contacts/customer": "provider:customer",
        "/contacts/customer/edit": "provider:customer",
    }
    for caller_path, expected in probes.items():
        resolved = get_bus().resolver.resolve("store", "get", caller_path)
        result = await _call(caller_path)
        assert resolved == expected
        assert result["invoked"] == expected == resolved
