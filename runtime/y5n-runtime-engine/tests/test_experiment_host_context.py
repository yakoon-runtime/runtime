"""Experiment (ADR-12): the host as a context consumer.

A host is an ordinary node: ``async def main()`` that reads its whole
invocation from ``context.current()`` — ``node.path`` for the target,
``workspace`` for the root, ``cwd`` for resolution, ``args`` for the
arguments — and then drives the target command's ``main()``.
"""

from __future__ import annotations

import inspect
import sys
import types
from pathlib import Path

import pytest
from y5n.runtime.api.flow.primitives import EmitView, Pulse, Stop
from y5n.runtime.engine.nodes import Node
from y5n.runtime.api.runtime import Event
from y5n.runtime.engine.flow import Flow, FlowCursor
from y5n.runtime.engine.runtime.invocation import derive_invocation_context
from y5n.sdk import context as sdk_context

# ---------------------------------------------------------------
# Helpers: a real target command as a module, like the packs
# ---------------------------------------------------------------


def _make_target_module(name: str, main) -> types.ModuleType:
    module = types.ModuleType(name)
    module.main = main
    sys.modules[name] = module
    return module


def _write_target_pack(root: Path) -> None:
    """Write a target command the host would resolve via ctx.node.path."""
    meta = root / "crm" / "contact" / "add" / ".yak" / "yak.yml"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(
        "\n".join(
            [
                "entry:",
                "  run: pack:_test_target_add:main",
            ]
        )
    )


# ---------------------------------------------------------------
# The host logic, expressed purely through the SDK context
# ---------------------------------------------------------------


def _drive_coroutine(coro):
    """The host's execution strategy — mirrors boot/python/runtime.py.

    The stepper is host-owned (ADR-12 Section 4): it stays in the host,
    it does not move into the flow engine.
    """

    async def _drive():
        if inspect.isasyncgen(coro):
            # A target main() written as an async generator yields Pulses
            # directly — drive it through the flow engine's own mechanism.
            gen = coro.__aiter__()
            val = await gen.__anext__()
            while True:
                try:
                    event = yield val
                    val = await gen.asend(event if event else None)
                except GeneratorExit:
                    break
                except StopAsyncIteration:
                    break
            yield Pulse()
            return

        gen = coro.__await__()
        try:
            val = gen.send(None)
        except StopIteration:
            yield Pulse()
            return

        while True:
            if not isinstance(val, Pulse):
                raise RuntimeError(
                    f"Unexpected yield from coroutine: {type(val).__name__}"
                )
            try:
                event = yield val
                val = gen.send(event if event else None)
            except GeneratorExit:
                break
            except StopIteration:
                break

        yield Pulse()

    return _drive()


class _Host:
    """A host as an ordinary node: parameterless main(), context-driven.

    Reads everything from context.current() — the exact values the boot
    host reads from ``space`` today — then interprets the target's entry
    and drives its main().
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def _read_entry(self, target_path: str) -> str | None:
        rel = target_path.strip("/")
        meta_file = self.root / rel / ".yak" / "yak.yml"
        if not meta_file.is_file():
            return None
        meta = _read_yaml(meta_file)
        return meta.get("entry", {}).get("run") if meta else None

    async def main(self):
        ctx = sdk_context.current()
        target_path = ctx.node.get("path")
        workspace = Path(ctx.workspace or ".")
        cwd = ctx.cwd

        entry = self._read_entry(target_path)
        if not entry:
            yield Pulse(effects=[EmitView(view={"kind": "text", "text": "no entry"})])
            return

        scheme, _, value = entry.partition(":")
        if scheme != "pack":
            yield Pulse(
                effects=[
                    EmitView(view={"kind": "text", "text": f"bad scheme {scheme}"})
                ]
            )
            return

        mod_name, _, func_name = value.rpartition(":")
        module = import_module(mod_name)
        main_fn = getattr(module, func_name, None)
        if main_fn is None:
            yield Pulse(effects=[EmitView(view={"kind": "text", "text": "no main"})])
            return

        # Pass the context down: the target main() sees the same context
        # the engine set for /crm/contact/add (tokens, session, ...).
        async for pulse in _drive_coroutine(main_fn()):
            yield pulse

        # workspace/cwd are consumed by the host (resolution); show that the
        # host read them from the context, not from a space object.
        yield Pulse(
            effects=[
                EmitView(
                    view={
                        "kind": "text",
                        "text": f"resolved:{workspace.name}:{cwd}",
                    }
                )
            ]
        )


def _make_parameterless_node(host: _Host) -> Node:
    add = Node(key="add", run=host.main)
    contact = Node(key="contact")
    contact.mount(add)
    crm = Node(key="crm")
    crm.mount(contact)
    return add


def _make_invoked_flow(harness, node: Node, tokens=None) -> Flow:
    flow_id = harness.session.next_flow_id()
    flow = Flow(
        id=flow_id,
        node=node,
        event=Event(payload="/crm/contact/add"),
        cursor=FlowCursor("run"),
        tokens=tokens or [],
        invocation=derive_invocation_context(
            node=node, session=harness.session, flow_id=flow_id, tokens=tokens or []
        ),
    )
    harness.session.add_flow(flow)
    return flow


# ---------------------------------------------------------------
# Tests
# ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_host_from_context_drives_target(tmp_path, harness, effect_executor):
    """A context-driven host resolves and drives a real target command."""

    _write_target_pack(tmp_path)
    harness.session.set_data("fs:root", str(tmp_path))
    harness.session.set_cwd("/crm/contact")

    async def target_main():
        # The target command reads the SAME context the engine set
        req = sdk_context.request()
        name = req.arg(0)
        yield Pulse(effects=[EmitView(view={"kind": "text", "text": f"hi {name}"})])
        yield Pulse()

    _make_target_module("_test_target_add", target_main)

    host = _Host(root=tmp_path)
    node = _make_parameterless_node(host)

    flow = _make_invoked_flow(harness, node, tokens=["jane"])
    harness.scheduler.schedule_flow(flow, harness.session)

    projections = effect_executor._on_projection

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    views = [c.kwargs["document"] for c in projections.call_args_list]
    assert views == [
        {"kind": "text", "text": "hi jane"},
        {"kind": "text", "text": f"resolved:{tmp_path.name}:/crm/contact"},
    ]


@pytest.mark.asyncio
async def test_host_from_context_missing_entry(tmp_path, harness, effect_executor):
    """No entry → the host reports it, still terminating cleanly."""

    harness.session.set_data("fs:root", str(tmp_path))
    host = _Host(root=tmp_path)
    node = _make_parameterless_node(host)

    flow = _make_invoked_flow(harness, node, tokens=["jane"])
    harness.scheduler.schedule_flow(flow, harness.session)

    projections = effect_executor._on_projection

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    views = [c.kwargs["document"] for c in projections.call_args_list]
    assert views == [{"kind": "text", "text": "no entry"}]


def _read_yaml(path: Path) -> dict:
    import yaml

    if path.is_file():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


def import_module(name: str):
    import importlib

    return importlib.import_module(name)


__all__ = []
