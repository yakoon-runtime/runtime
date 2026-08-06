"""Regression: does cd's CwdEffect reach the session through the real host?

Full path: user types "cd /foo" → engine dispatches the cd node (host:
/boot/python/runtime) → _next_step derives the invocation context from the
session → the host stepper drives cd.main() → cd yields a CwdEffect → the
engine must apply it so the next command sees the new cwd.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from y5n.runtime.api.flow.primitives import CwdEffect, EmitView, Pulse, Stop
from y5n.runtime.engine.nodes import Node
from y5n.runtime.api.runtime import Event
from y5n.runtime.engine.executor.base import ExecutorKind, ExecutorRegistry
from y5n.runtime.engine.executor.runtime import RuntimeExecutor
from y5n.runtime.engine.flow import Flow, FlowCursor
from y5n.runtime.engine.machine.parser import InputParser
from y5n.runtime.engine.machine.runner import Runner
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.runtime.invocation import derive_invocation_context
from y5n.sdk import context as sdk_context


def _make_module(name: str, main) -> types.ModuleType:
    module = types.ModuleType(name)
    module.main = main  # type: ignore[attr-defined]
    sys.modules[name] = module
    return module


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_tree(root: Path, cd_main) -> Tree:
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=root, executors=registry)
    tree.build()
    return tree


class _Chdir:
    def __init__(self, path: str) -> None:
        self._path = path

    def __await__(self):
        yield Pulse(effects=[CwdEffect(self._path)])
        return None


class _Write:
    def __await__(self):
        yield Pulse(effects=[EmitView(view={"kind": "text", "text": "ok"})])
        return None


def _make_cd_main():

    async def cd_main():
        from y5n.sdk import context

        req = context.request()
        target = req.arg(0)
        await _Chdir(target)
        await _Write()

    _make_module("_cd_entry", cd_main)


@pytest.mark.asyncio
async def test_real_cd_module(tmp_path, harness, effect_executor):
    """The real cd.py module through the full engine path."""

    import y5n.packs.system.cd as real_cd

    # patch fs.chdir to capture the display path instead of touching session
    captured = {}

    class _FakeFS:
        async def chdir(self, path):
            captured["path"] = path

    real_cd.fs = _FakeFS()  # type: ignore[assignment]

    _make_module("_cd_entry", real_cd.main)

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
        tmp_path / "cd" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Cd",
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:_cd_entry:main",
            ]
        ),
    )

    tree = _build_tree(tmp_path, None)
    (tmp_path / "opt").mkdir()
    harness.session.set_data("fs:root", str(tmp_path))
    harness.session.set_cwd("/")

    parser = InputParser()
    cd_node = tree.find("/cd")

    def resolve_node(*, key, tokens, session, strict=True):
        if key == "cd":
            return cd_node, tokens or []
        return None, tokens or []

    harness.engine.on_parse_input = parser.parse
    harness.engine.on_resolve_command = resolve_node

    async def on_dispatch(*, session, event):
        flow = await harness.engine.dispatch(session=session, event=event)
        if flow:
            harness.scheduler.schedule_flow(flow, harness.session)

    runner = Runner(
        session=harness.session,
        on_dispatch=on_dispatch,
        on_schedule_flow=harness.scheduler.schedule_flow,
    )
    await runner.on_input(Event(payload="cd /opt"))

    flows = list(harness.session.flows())
    assert flows, "no flow created"
    pulse = await harness.run_until_blocked(flows[0])
    assert isinstance(pulse.control, Stop)

    # The real cd.py must have computed /opt (from cwd="/") and called chdir
    assert captured.get("path") == "/opt", f"cd called chdir({captured.get('path')!r})"


@pytest.mark.asyncio
async def test_cd_through_full_engine(tmp_path, harness, effect_executor):
    """cd via host: node → CwdEffect applied → next command sees /foo."""

    _make_cd_main()

    # boot host node
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

    # cd node with host: and a real entry
    _write(
        tmp_path / "cd" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Cd",
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:_cd_entry:main",
            ]
        ),
    )

    tree = _build_tree(tmp_path, None)

    harness.session.set_data("fs:root", str(tmp_path))
    harness.session.set_cwd("/home")

    cd_node = tree.find("/cd")
    assert cd_node is not None, "cd node not found in tree"

    # dispatch + step via engine
    flow = _make_flow(cd_node, harness.session, tokens=["/foo"])
    harness.scheduler.schedule_flow(flow, harness.session)
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)

    assert harness.session.cwd == "/foo", f"session.cwd = {harness.session.cwd!r}"


@pytest.mark.asyncio
async def test_cd_then_pwd_full_engine(tmp_path, harness, effect_executor):
    """After cd, the next command's context must carry the new cwd."""

    _make_cd_main()

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
        tmp_path / "cd" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Cd",
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:_cd_entry:main",
            ]
        ),
    )
    _write(
        tmp_path / "pwd" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Pwd",
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:_pwd_entry:main",
            ]
        ),
    )

    async def pwd_main():
        from y5n.sdk import context

        seen.append(context.current().cwd)
        await _Write()

    _make_module("_pwd_entry", pwd_main)

    tree = _build_tree(tmp_path, None)
    harness.session.set_data("fs:root", str(tmp_path))
    harness.session.set_cwd("/home")

    seen: list[str] = []

    # cd /foo
    cd_node = tree.find("/cd")
    flow = _make_flow(cd_node, harness.session, tokens=["/foo"])
    harness.scheduler.schedule_flow(flow, harness.session)
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)

    # pwd (next command)
    pwd_node = tree.find("/pwd")
    flow2 = _make_flow(pwd_node, harness.session, tokens=[])
    harness.scheduler.schedule_flow(flow2, harness.session)
    pulse = await harness.run_until_blocked(flow2)
    assert isinstance(pulse.control, Stop)

    assert harness.session.cwd == "/foo", f"session.cwd = {harness.session.cwd!r}"
    assert seen == ["/foo"], f"pwd saw cwd {seen!r}"


@pytest.mark.asyncio
async def test_invocation_is_a_dispatch_snapshot(harness, effect_executor):
    """ADR-12 Invocation lifetime: the conditions of the start.

    The context is an immutable snapshot established at dispatch — it does
    not track later session mutations. A flow that yields a CwdEffect must
    NOT see the new cwd through context.current() in a later step of the
    SAME flow (that would be a live projection). The next command (a new
    flow) gets a fresh snapshot.
    """

    harness.session.set_data("fs:root", "/tmp/ws")
    harness.session.set_cwd("/home")

    seen_after_mutation = []

    async def handler():
        # read the invocation snapshot BEFORE the mutation
        before = sdk_context.current().cwd
        yield Pulse(effects=[CwdEffect("/foo")])
        # read again AFTER the mutation, still in the same flow
        after = sdk_context.current().cwd
        seen_after_mutation.append((before, after))
        yield Pulse()

    node = Node(key="cd", run=handler)
    flow = _make_flow(node, harness.session, tokens=["/foo"])
    harness.scheduler.schedule_flow(flow, harness.session)

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)

    # Model A: both reads see the dispatch-time snapshot ("/home")
    assert seen_after_mutation == [("/home", "/home")], seen_after_mutation
    # but the session itself WAS mutated
    assert harness.session.cwd == "/foo"


@pytest.mark.asyncio
async def test_next_command_sees_fresh_snapshot(harness, effect_executor):
    """The next command is a new flow with a fresh invocation snapshot."""

    harness.session.set_data("fs:root", "/tmp/ws")
    harness.session.set_cwd("/home")

    async def cd_handler():
        yield Pulse(effects=[CwdEffect("/foo")])
        yield Pulse()

    async def pwd_handler():
        seen.append(sdk_context.current().cwd)
        yield Pulse()

    seen = []
    cd_node = Node(key="cd", run=cd_handler)
    flow = _make_flow(cd_node, harness.session, tokens=["/foo"])
    harness.scheduler.schedule_flow(flow, harness.session)
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)

    pwd_node = Node(key="pwd", run=pwd_handler)
    flow2 = _make_flow(pwd_node, harness.session, tokens=[])
    harness.scheduler.schedule_flow(flow2, harness.session)
    pulse = await harness.run_until_blocked(flow2)
    assert isinstance(pulse.control, Stop)

    assert seen == ["/foo"], f"next command saw {seen!r}"


@pytest.mark.asyncio
async def test_real_input_cd_opt(tmp_path, harness, effect_executor):
    """The real input path: 'cd /opt' parsed, dispatched, applied.

    This mirrors what the user types. The parser splits 'cd /opt' into
    cmd='cd', args=['/opt']; dispatch resolves the node and the host runs
    cd.main(); the CwdEffect must update the session so a following
    command sees /opt.
    """

    _make_cd_main()
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
        tmp_path / "cd" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Cd",
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:_cd_entry:main",
            ]
        ),
    )

    tree = _build_tree(tmp_path, None)
    harness.session.set_data("fs:root", str(tmp_path))
    harness.session.set_cwd("/")

    parser = InputParser()
    cmd, args, _ = parser.parse(Event(payload="cd /opt"))
    assert cmd == "cd"
    assert args == ["/opt"]

    cd_node = tree.find("/cd")
    assert cd_node is not None

    # wire the engine's resolve + parse, like build_runtime does
    def resolve_node(*, key, tokens, session, strict=True):
        if key == "cd":
            return cd_node, tokens or []
        return None, tokens or []

    harness.engine.on_parse_input = parser.parse
    harness.engine.on_resolve_command = resolve_node

    async def on_dispatch(*, session, event):
        flow = await harness.engine.dispatch(session=session, event=event)
        if flow:
            harness.scheduler.schedule_flow(flow, harness.session)

    runner = Runner(
        session=harness.session,
        on_dispatch=on_dispatch,
        on_schedule_flow=harness.scheduler.schedule_flow,
    )
    await runner.on_input(Event(payload="cd /opt"))

    flows = list(harness.session.flows())
    assert flows, "no flow created"
    flow = flows[0]
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)

    assert harness.session.cwd == "/opt", f"session.cwd = {harness.session.cwd!r}"


def _make_flow(node, session, tokens=None):

    flow_id = session.next_flow_id()
    flow = Flow(
        id=flow_id,
        node=node,
        event=Event(payload=node.key),
        cursor=FlowCursor("run"),
        tokens=tokens or [node.key],
        invocation=derive_invocation_context(
            node=node, session=session, flow_id=flow_id, tokens=tokens or []
        ),
    )
    session.add_flow(flow)
    return flow
