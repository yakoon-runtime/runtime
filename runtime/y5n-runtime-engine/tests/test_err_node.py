"""err command — end-to-end against the real engine path.

Proves the invariant "an error creates a new invocation" at the
command level: the engine routes an exception to /usr/bin/err, the
invocation context carries the error payload, and err.main() projects
the matching template through the SDK ports (runtime.resolve, jinja,
compile) — the same way any command renders its output.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from y5n.runtime.api.flow.primitives import EmitView
from y5n.runtime.api.runtime import get_bus, set_bus
from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.runtime.invocation import (
    derive_invocation_context,
    establish_invocation_context,
)
from y5n.runtime.engine.wire.adapter.callable import CallableAdapter
from y5n.runtime.engine.wire.adapter.resource import ResourceAdapter
from y5n.runtime.engine.wire.document import build_document_stack
from y5n.sdk import context as sdk_context


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_tree(root: Path) -> Tree:
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=root, executors=registry)
    tree.build()
    return tree


@pytest.fixture
async def bus(monkeypatch):
    monkeypatch.setenv("YAK_ENDPOINT", "inprocess://")

    from y5n.runtime.api.runtime.bus import _make_default_bus

    previous = get_bus()
    bus = _make_default_bus()
    set_bus(bus)
    yield bus
    set_bus(previous)


async def _wire_bus(bus, tree) -> None:
    doc = build_document_stack(tree=tree)

    bus.resolver.register(
        "system:projection",
        {"jinja": ["__call__"]},
        path="/",
    )
    bus.transport.register_adapter(
        "jinja",
        CallableAdapter(doc.jinja.render_str),
    )

    bus.resolver.register(
        "system:projection",
        {"compile": ["__call__"]},
        path="/",
    )
    bus.transport.register_adapter(
        "compile",
        CallableAdapter(doc.compiler.compile),
    )

    bus.resolver.register(
        "system:projection",
        {"runtime.resource": ["resolve"]},
        path="/",
    )
    bus.transport.register_adapter(
        "runtime.resource",
        ResourceAdapter(tree),
    )


async def _run_err(tmp_path: Path, harness, bus, error: dict) -> list[dict]:
    """Build the tree, establish an error invocation, drive err.main().

    Returns the emitted projections (EmitView views).
    """

    # boot host (Python runtime) + /usr/bin/err (real entry)
    _write(
        tmp_path / "boot" / "python" / "runtime" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Python Runtime Host",
                "entry:",
                "  run: pack:y5n.runtime.boot.python.runtime:main",
                "resolve:",
                "  default: pack:y5n.runtime.boot.python.runtime:resolve",
            ]
        ),
    )
    _write(
        tmp_path / "usr" / "bin" / "err" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Err",
                "host: /boot/python/runtime",
                "anonymous: true",
                "entry:",
                "  run: pack:y5n.packs.system.err:main",
                "resources:",
                "  ref: resource:y5n.packs.system.resources.loader:content",
                "  error:",
                "    default:",
                "      path: err/error.ydf",
                "    not_found:",
                "      path: err/not_found.ydf",
                "    denied:",
                "      path: err/denied.ydf",
                "    elevation:",
                "      path: err/elevation.ydf",
            ]
        ),
    )

    tree = _build_tree(tmp_path)
    err_node = tree.find("/usr/bin/err")
    assert err_node is not None, "err node not found in tree"

    await _wire_bus(bus, tree)
    harness.session.set_data("fs:root", str(tmp_path))

    # The engine routes an exception to /usr/bin/err; the invocation
    # context carries the error payload (what _route_error produces).
    flow = derive_invocation_context(
        node=err_node,
        session=harness.session,
        flow_id=harness.session.next_flow_id(),
        tokens=[],
        error=error,
    )
    establish_invocation_context(flow)

    assert sdk_context.error() == error

    # drive err.main() like the host stepper does; collect EmitView
    import y5n.packs.system.err as err_cmd

    emitted: list[dict] = []
    gen = err_cmd.main().__await__()
    try:
        val = gen.send(None)
        while True:
            from y5n.runtime.api.flow.primitives import Pulse

            assert isinstance(val, Pulse)
            for effect in val.effects or []:
                if isinstance(effect, EmitView):
                    emitted.append(effect.view)
            val = gen.send(None)
    except StopIteration:
        pass

    return emitted


def _projection_text(views: list[dict]) -> str:
    def _text_of(parts) -> str:
        out = ""
        for p in parts or []:
            if isinstance(p, dict):
                out += p.get("text", "") or _text_of(p.get("children"))
            else:
                out += str(p)
        return out

    blocks = (views[0] or {}).get("blocks", []) if views else []
    return " ".join(_text_of(b.get("text")) for b in blocks)


@pytest.mark.asyncio
async def test_err_renders_node_not_found(tmp_path, harness, bus):
    """NodeNotFound im Invocation-Context -> err.main() projiziert not_found."""

    views = await _run_err(
        tmp_path,
        harness,
        bus,
        {
            "type": "NodeNotFound",
            "message": "NodeNotFound",
            "command": "does-not-exist",
            "suggestions": [],
        },
    )

    text = _projection_text(views)
    assert "does-not-exist" in text
    assert "not found" in text


@pytest.mark.asyncio
async def test_err_renders_permission_denied(tmp_path, harness, bus):
    """PermissionDenied im Invocation-Context -> err.main() projiziert denied."""

    views = await _run_err(
        tmp_path,
        harness,
        bus,
        {
            "type": "PermissionDenied",
            "message": "PermissionDenied",
        },
    )

    text = _projection_text(views)
    assert "denied" in text.lower() or "Access Denied" in text


@pytest.mark.asyncio
async def test_err_renders_elevation_required(tmp_path, harness, bus):
    """ElevationRequired im Invocation-Context -> err.main() projiziert elevation."""

    views = await _run_err(
        tmp_path,
        harness,
        bus,
        {
            "type": "ElevationRequired",
            "message": "Elevation required",
            "command": "account/delete",
        },
    )

    text = _projection_text(views)
    assert "elevation" in text.lower()
