from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from y5n.runtime.api.resources import Resource
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.wire.adapter.document import DocumentAdapter
from y5n.runtime.engine.wire.adapter.resource import ResourceAdapter


def _make_module(name: str, funcs: dict) -> types.ModuleType:
    module = types.ModuleType(name)
    for fname, fn in funcs.items():
        setattr(module, fname, fn)
    sys.modules[name] = module
    return module


def _build_tree(root: Path) -> Tree:
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=root, executors=registry)
    tree.build()
    return tree


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _fake_node(**kwargs) -> types.SimpleNamespace:
    defaults = {"key": "app", "resources": {}, "fs_path": None}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


# ----------------------------------
# TREE: RAW REFERENCES + RESOLVE HANDLER
# ----------------------------------


@pytest.mark.asyncio
async def test_tree_stores_raw_references_and_builds_resolve(tmp_path: Path):
    _write(
        tmp_path / "boot" / "python" / "runtime" / ".yak" / "yak.yml",
        "\n".join(
            [
                "entry:",
                "  run: pack:x:run",
                "resolve:",
                "  default: pack:x:resolve",
            ]
        ),
    )
    _write(
        tmp_path / "app" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: App",
                "host: /boot/python/runtime",
                "man:",
                "  default: file:resources/man.ydf",
            ]
        ),
    )
    tree = _build_tree(tmp_path)

    host = tree.find("/boot/python/runtime")
    assert host is not None
    assert host.resolve is not None

    app = tree.find("/app")
    assert app is not None
    assert app.resources == {"man": {"default": "file:resources/man.ydf"}}
    assert app.resolve is None


# ----------------------------------------
# RUNTIME.RESOURCE DISPATCHES TO THE HOST
# ----------------------------------------


@pytest.mark.asyncio
async def test_runtime_resource_dispatches_to_host(tmp_path: Path):
    async def host_resolve(node, capability, parameters=None):
        expr = (node.resources or {}).get(capability, {}).get("default")
        return Resource.text(f"resolved:{capability}:{expr}")

    _make_module("_test_host_resolve", {"resolve": host_resolve})
    _write(
        tmp_path / "boot" / "python" / "runtime" / ".yak" / "yak.yml",
        "\n".join(
            [
                "entry:",
                "  run: pack:x:run",
                "resolve:",
                "  default: pack:_test_host_resolve:resolve",
            ]
        ),
    )
    _write(
        tmp_path / "app" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: App",
                "host: /boot/python/runtime",
                "man:",
                "  default: resource:y5n.packs.system.app:man",
            ]
        ),
    )
    tree = _build_tree(tmp_path)
    adapter = ResourceAdapter(tree)
    call = Call(
        port="runtime.resource",
        method="resolve",
        args={},
        caller_path="/app",
        caller_session_key="session-1",
    )
    resource = await adapter.resolve(call, node_path="/app", capability="man")
    assert resource.read_text() == "resolved:man:resource:y5n.packs.system.app:man"


@pytest.mark.asyncio
async def test_runtime_resource_supports(tmp_path: Path):
    async def host_resolve(node, capability, parameters=None):
        return Resource.text("x")

    _make_module("_test_host_supports", {"resolve": host_resolve})
    _write(
        tmp_path / "boot" / "python" / "runtime" / ".yak" / "yak.yml",
        "\n".join(
            [
                "entry:",
                "  run: pack:x:run",
                "resolve:",
                "  default: pack:_test_host_supports:resolve",
            ]
        ),
    )
    _write(
        tmp_path / "app" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: App",
                "host: /boot/python/runtime",
                "man:",
                "  default: file:resources/man.ydf",
            ]
        ),
    )
    tree = _build_tree(tmp_path)
    adapter = ResourceAdapter(tree)
    call = Call(
        port="runtime.resource",
        method="supports",
        args={},
        caller_path="/app",
        caller_session_key="session-1",
    )
    assert await adapter.supports(call, node_path="/app", capability="man") is True
    assert await adapter.supports(call, node_path="/app", capability="logo") is False


# ----------------------------------------
# PARALLEL HOSTS — EACH RESOLVES ITS OWN
# ----------------------------------------


@pytest.mark.asyncio
async def test_parallel_hosts_resolve_their_own_nodes(tmp_path: Path):
    async def python_resolve(node, capability, parameters=None):
        return Resource.text(f"python:{capability}")

    async def ticker_resolve(node, capability, parameters=None):
        return Resource.text(f"ticker:{capability}")

    _make_module("_test_parallel_py", {"resolve": python_resolve})
    _make_module("_test_parallel_tick", {"resolve": ticker_resolve})

    for host_path, mod in (
        ("python", "_test_parallel_py"),
        ("ticker", "_test_parallel_tick"),
    ):
        _write(
            tmp_path / "boot" / host_path / "runtime" / ".yak" / "yak.yml",
            "\n".join(
                [
                    "entry:",
                    "  run: pack:x:run",
                    "resolve:",
                    f"  default: pack:{mod}:resolve",
                ]
            ),
        )

    for app, host in (("app1", "python"), ("app2", "ticker")):
        _write(
            tmp_path / app / ".yak" / "yak.yml",
            "\n".join(
                [
                    f"title: {app}",
                    f"host: /boot/{host}/runtime",
                    "man:",
                    "  default: file:resources/man.ydf",
                ]
            ),
        )

    tree = _build_tree(tmp_path)
    adapter = ResourceAdapter(tree)
    call = Call(
        port="runtime.resource",
        method="resolve",
        args={},
        caller_path="/",
        caller_session_key="session-1",
    )
    r1 = await adapter.resolve(call, node_path="/app1", capability="man")
    r2 = await adapter.resolve(call, node_path="/app2", capability="man")
    assert r1.read_text() == "python:man"
    assert r2.read_text() == "ticker:man"


# ----------------------------------------
# PYTHON HOST RESOLVE (file: / resource:)
# ----------------------------------------


@pytest.mark.asyncio
async def test_python_host_resolve_file(tmp_path: Path):
    from y5n.runtime.boot.python.runtime import resolve as host_resolve

    (tmp_path / "man.ydf").write_text("# Man")
    node = _fake_node(
        resources={"man": {"default": "file:man.ydf"}},
        fs_path=tmp_path,
    )
    resource = await host_resolve(node, "man")
    assert resource.read_text() == "# Man"
    assert resource.read_bytes() == b"# Man"


@pytest.mark.asyncio
async def test_python_host_resolve_capability():
    from y5n.runtime.boot.python.runtime import resolve as host_resolve

    def man(**params):
        return Resource.text("man " + params.get("lang", "en"))

    module = _make_module("_test_pyhost_cap", {"man": man})
    node = _fake_node(resources={"man": {"default": f"resource:{module.__name__}:man"}})
    resource = await host_resolve(node, "man", parameters={"lang": "de"})
    assert resource.read_text() == "man de"


@pytest.mark.asyncio
async def test_python_host_resolve_variant():
    from y5n.runtime.boot.python.runtime import resolve as host_resolve

    node = _fake_node(
        resources={
            "man": {
                "de": "file:man_de.ydf",
                "default": "file:man.ydf",
            }
        },
        fs_path=Path("/nonexistent"),
    )
    resource = await host_resolve(node, "man", parameters={"lang": "de"})
    with pytest.raises(FileNotFoundError, match="man_de"):
        resource.read_text()


@pytest.mark.asyncio
async def test_python_host_resolve_missing():
    from y5n.runtime.boot.python.runtime import resolve as host_resolve

    node = _fake_node(resources={})
    with pytest.raises(LookupError, match="man"):
        await host_resolve(node, "man")


@pytest.mark.asyncio
async def test_python_host_resolve_declared_parameters():
    from y5n.runtime.boot.python.runtime import resolve as host_resolve

    def load(path: str, **params):
        return Resource.text(f"loaded:{path}:{params.get('lang', 'en')}")

    module = _make_module("_test_pyhost_params", {"load": load})
    node = _fake_node(
        resources={
            "man": {
                "default": {
                    "ref": f"resource:{module.__name__}:load",
                    "parameters": {"path": "info/man.ydf"},
                }
            }
        }
    )
    resource = await host_resolve(node, "man", parameters={"lang": "de"})
    assert resource.read_text() == "loaded:info/man.ydf:de"


@pytest.mark.asyncio
async def test_tree_stores_resources_strategy(tmp_path: Path):
    _write(
        tmp_path / "app" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: App",
                "host: /boot/python/runtime",
                "resources:",
                "  ref: resource:y5n.packs.system.resources.loader:content",
                "  man:",
                "    default:",
                "      path: info/man.ydf",
                "  document:",
                "    de:",
                "      path: info/de.ydf",
            ]
        ),
    )
    tree = _build_tree(tmp_path)
    app = tree.find("/app")
    assert app is not None
    assert app.resources == {
        "ref": "resource:y5n.packs.system.resources.loader:content",
        "man": {"default": {"path": "info/man.ydf"}},
        "document": {"de": {"path": "info/de.ydf"}},
    }


@pytest.mark.asyncio
async def test_python_host_resolve_resources_strategy():
    from y5n.runtime.boot.python.runtime import resolve as host_resolve

    node = _fake_node(
        resources={
            "ref": "resource:y5n.packs.system.resources.loader:content",
            "man": {"default": {"path": "info/man.ydf"}},
            "document": {"default": {"path": "info/default.ydf"}},
        }
    )
    resource = await host_resolve(node, "man", parameters={"lang": "de"})
    assert resource.read_text()  # resolves via the strategy loader
    resource = await host_resolve(node, "document")
    assert resource.read_text()


@pytest.mark.asyncio
async def test_python_host_resolve_passes_capability_and_variant():
    from y5n.runtime.boot.python.runtime import resolve as host_resolve

    def strategy(capability, variant, **params):
        return Resource.text(f"{capability}:{variant}:{params.get('path')}")

    module = _make_module("_test_pyhost_strategy", {"content": strategy})
    node = _fake_node(
        resources={
            "ref": f"resource:{module.__name__}:content",
            "man": {
                "default": {"path": "info/man.ydf"},
                "de": {"path": "info/man_de.ydf"},
            },
        }
    )
    resource = await host_resolve(node, "man", parameters={"lang": "de"})
    assert resource.read_text() == "man:de:info/man_de.ydf"


# ----------------------------------------
# DOCUMENT ADAPTER DISPATCHES TO THE HOST
# ----------------------------------------


class FakeProjector:
    def on_render_str(self, template: str, context: dict) -> str:
        return f"<{template}>"

    def on_compile(self, text: str, context: dict) -> dict:
        return {
            "kind": "document",
            "header": {"role": "info"},
            "blocks": [{"type": "text", "text": [{"type": "text", "text": text}]}],
        }


@pytest.mark.asyncio
async def test_document_adapter_dispatches(tmp_path: Path):
    async def host_resolve(node, capability, parameters=None):
        expr = (node.resources or {}).get(capability, {}).get("default")
        path = Path(node.fs_path) / expr[len("file:") :]
        return Resource.path(path)

    _make_module("_test_doc_host", {"resolve": host_resolve})
    _write(
        tmp_path / "boot" / "python" / "runtime" / ".yak" / "yak.yml",
        "\n".join(
            [
                "entry:",
                "  run: pack:x:run",
                "resolve:",
                "  default: pack:_test_doc_host:resolve",
            ]
        ),
    )
    _write(
        tmp_path / "app" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: App",
                "host: /boot/python/runtime",
                "document:",
                "  default: file:default.ydf",
            ]
        ),
    )
    (tmp_path / "app" / "default.ydf").write_text("hello")
    tree = _build_tree(tmp_path)

    import json

    adapter = DocumentAdapter(FakeProjector(), tree)
    call = Call(
        port="document",
        method="render",
        args={},
        caller_path="/app",
        caller_session_key="session-1",
    )
    result = json.loads(await adapter.render(call))
    assert result["blocks"][0]["text"][0]["text"] == "<hello>"
    assert result["id"]  # normalize stamps the document id


@pytest.mark.asyncio
async def test_document_adapter_variant_survives_state_collision(tmp_path: Path):
    """The variant selector (name=...) wins over a colliding template state.

    A template renders ``{{ name }}``; the same key must not clobber the
    variant selector that picks the resource. Regression: state={"name": ...}
    used to override name="denied", so the variant fell back to default.
    """

    async def host_resolve(node, capability, parameters=None):
        variants = (node.resources or {}).get(capability, {})
        selector = parameters or {}
        chosen = None
        for key in ("lang", "variant", "name"):
            value = selector.get(key)
            if value and value in variants:
                chosen = variants[value]
                break
        if chosen is None:
            chosen = variants.get("default")
        if not isinstance(chosen, dict):
            return None
        expr = chosen.get("path")
        path = Path(node.fs_path) / expr
        return Resource.path(path)

    _make_module("_test_doc_variant_host", {"resolve": host_resolve})
    _write(
        tmp_path / "boot" / "python" / "runtime" / ".yak" / "yak.yml",
        "\n".join(
            [
                "entry:",
                "  run: pack:x:run",
                "resolve:",
                "  default: pack:_test_doc_variant_host:resolve",
            ]
        ),
    )
    _write(
        tmp_path / "app" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: App",
                "host: /boot/python/runtime",
                "document:",
                "  default:",
                "    path: default.ydf",
                "  denied:",
                "    path: denied.ydf",
            ]
        ),
    )
    (tmp_path / "app" / "default.ydf").write_text("deleted {{ name }}")
    (tmp_path / "app" / "denied.ydf").write_text("cannot delete {{ name }}")
    tree = _build_tree(tmp_path)

    import json

    adapter = DocumentAdapter(FakeProjector(), tree)
    call = Call(
        port="document",
        method="render",
        args={},
        caller_path="/app",
        caller_session_key="session-1",
    )

    denied = json.loads(
        await adapter.render(call, name="denied", state={"name": "root"})
    )
    assert denied["blocks"][0]["text"][0]["text"] == "<cannot delete {{ name }}>"

    default = json.loads(
        await adapter.render(call, name="default", state={"name": "lara"})
    )
    assert default["blocks"][0]["text"][0]["text"] == "<deleted {{ name }}>"
