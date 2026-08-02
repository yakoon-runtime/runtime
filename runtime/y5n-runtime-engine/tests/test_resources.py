from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from y5n.runtime.api.resources import Resource
from y5n.runtime.api.runtime.context import Call
from y5n.runtime.engine.resources.resolver import PythonResourceResolver
from y5n.runtime.engine.wire.adapter.resource import ResourceAdapter


def _make_module(name: str, funcs: dict) -> types.ModuleType:
    module = types.ModuleType(name)
    for fname, fn in funcs.items():
        setattr(module, fname, fn)
    sys.modules[name] = module
    return module


@pytest.fixture
def resolver() -> PythonResourceResolver:
    return PythonResourceResolver()


@pytest.mark.asyncio
async def test_supports(resolver: PythonResourceResolver):
    assert resolver.supports("file:resources/man.ydf")
    assert resolver.supports("resource:y5n.packs.system.info:man")
    assert not resolver.supports("http://example.com/man")
    assert not resolver.supports("nonsense")


@pytest.mark.asyncio
async def test_file_resolve(resolver: PythonResourceResolver, tmp_path: Path):
    (tmp_path / "man.ydf").write_text("# Man")
    resource = await resolver.resolve("file:man.ydf", base=tmp_path)
    assert resource.read_text() == "# Man"
    assert resource.read_bytes() == b"# Man"


@pytest.mark.asyncio
async def test_file_requires_base(resolver: PythonResourceResolver):
    with pytest.raises(LookupError, match="base"):
        await resolver.resolve("file:man.ydf")


@pytest.mark.asyncio
async def test_capability_resolve_resource(
    resolver: PythonResourceResolver,
):
    module = _make_module(
        "_test_res_capability",
        {"man": lambda **params: Resource.text("man " + params.get("lang", "en"))},
    )
    resource = await resolver.resolve(
        f"resource:{module.__name__}:man",
        parameters={"lang": "de"},
    )
    assert resource.read_text() == "man de"


@pytest.mark.asyncio
async def test_capability_coerces_str(resolver: PythonResourceResolver):
    module = _make_module("_test_res_coerce", {"man": lambda **params: "plain text"})
    resource = await resolver.resolve(f"resource:{module.__name__}:man")
    assert resource.read_text() == "plain text"
    assert resource.read_bytes() == b"plain text"


@pytest.mark.asyncio
async def test_capability_awaitable(resolver: PythonResourceResolver):
    async def _async_man(**params):
        return Resource.text("async")

    module = _make_module("_test_res_async", {"man": _async_man})
    resource = await resolver.resolve(f"resource:{module.__name__}:man")
    assert resource.read_text() == "async"


@pytest.mark.asyncio
async def test_capability_missing(resolver: PythonResourceResolver):
    _make_module("_test_res_missing", {})
    with pytest.raises(LookupError, match="capability"):
        await resolver.resolve("resource:_test_res_missing:man")


class FakeNode:
    fs_path: Path


class FakeTree:
    def __init__(self, node: FakeNode) -> None:
        self._node = node

    def find(self, path: str) -> FakeNode:
        return self._node


@pytest.mark.asyncio
async def test_adapter_resolve_file(tmp_path: Path):
    (tmp_path / "help.ydf").write_text("# Help")

    node = FakeNode()
    node.fs_path = tmp_path
    adapter = ResourceAdapter(PythonResourceResolver(), FakeTree(node))
    call = Call(
        port="runtime.resource",
        method="resolve",
        args={},
        caller_path="/fake",
        caller_session_key="session-1",
    )
    resource = await adapter.resolve(call, ref="file:help.ydf")
    assert resource.read_text() == "# Help"


@pytest.mark.asyncio
async def test_adapter_supports():
    adapter = ResourceAdapter(PythonResourceResolver(), FakeTree(FakeNode()))
    call = Call(
        port="runtime.resource",
        method="supports",
        args={},
        caller_path="/fake",
        caller_session_key="session-1",
    )
    assert await adapter.supports(call, ref="file:x") is True
    assert await adapter.supports(call, ref="http://x") is False
