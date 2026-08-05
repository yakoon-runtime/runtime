"""Phase 1 experiment (ADR-12): Context as the single ABI.

Every entry point is ``async def main()`` — no parameters. Production is
already there: all packs declare ``async def main():`` (98 occurrences),
and the boot host already invokes ``main_fn()`` without arguments
(``boot/python/runtime.py``).

This experiment proves the target shape end-to-end: a parameterless
``main()`` reads everything from ``context.current()`` (which the host sets
first) and runs through the flow engine with the same write → prompt →
reply → stop round trip as today.

If this works, ``NodeSpace`` is only a pass-through object and can disappear:
the engine sets the context, the host reads it, nothing in between.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.primitives import AwaitEvent, EmitView, Pulse, Stop
from y5n.runtime.api.nodes import Node
from y5n.runtime.api.runtime.context import set_context
from y5n.sdk import context as sdk_context


def _set_test_context() -> None:
    """Set the raw invocation context exactly as the engine would."""
    set_context(
        {
            "node": {"path": "/crm/contact/add", "name": "add"},
            "cwd": "/crm/contact",
            "workspace": "/tmp/workspace",
            "user": {"id": "u-1", "name": "alice"},
            "session": {"key": "s-1", "lang": "en", "interaction": "cli"},
            "flow": {"id": "f-1", "key": "add"},
            "tokens": ["/crm/contact/add", "jane"],
        }
    )


def _parameterless(handler):
    """Adapter: call ``main()`` with no arguments, discarding the ctx.

    This is exactly what the boot host does today (``main_fn()``).
    """

    def _run(ctx):
        return handler()

    return _run


def _make_node(main):
    return Node(key="test", run=_parameterless(main))


@pytest.mark.asyncio
async def test_main_parameterless_reads_context(harness, effect_executor):
    """A parameterless main() that reads context.current() flows through."""

    async def main():
        ctx = sdk_context.current()
        assert ctx.node.get("path") == "/crm/contact/add"
        assert ctx.tokens == ["/crm/contact/add", "jane"]

        req = sdk_context.request()
        assert req.arg(0) == "jane"

        yield Pulse(effects=[EmitView(view={"kind": "text", "text": "ok"})])
        yield Pulse()

    _set_test_context()
    node = _make_node(main)

    from support.flow import make_flow

    flow = make_flow(node.run, session=harness.session)
    harness.scheduler.schedule_flow(flow, harness.session)

    projections = effect_executor._on_projection

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    views = [c.kwargs["document"] for c in projections.call_args_list]
    assert views == [{"kind": "text", "text": "ok"}]


@pytest.mark.asyncio
async def test_main_parameterless_prompt_round_trip(harness, effect_executor):
    """Parameterless main(): write → AwaitEvent → reply → stop."""

    async def main():
        yield Pulse(effects=[EmitView(view={"kind": "text", "text": "write-view"})])
        event = yield Pulse(control=AwaitEvent("__user__", scope=Scope.USER_INPUT))
        assert event is not None
        yield Pulse(
            effects=[EmitView(view={"kind": "text", "text": f"got:{event.payload}"})]
        )
        yield Pulse()

    _set_test_context()
    node = _make_node(main)

    from support.flow import make_flow

    flow = make_flow(node.run, session=harness.session)
    harness.scheduler.schedule_flow(flow, harness.session)

    projections = effect_executor._on_projection

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, AwaitEvent), f"got {pulse.control!r}"
    assert projections.call_count == 1

    harness.send_user_input(flow, "hi")
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)

    views = [c.kwargs["document"] for c in projections.call_args_list]
    assert views == [
        {"kind": "text", "text": "write-view"},
        {"kind": "text", "text": "got:hi"},
    ]


@pytest.mark.asyncio
async def test_host_reads_its_whole_needs_from_context(harness, effect_executor):
    """A host-shaped main(): every value today read from ``space`` comes
    from ``context.current()`` instead.

    This mirrors the boot host's `run(space)`: it reads space.path,
    space.session (fs:root, cwd), and space.request.args() — all of which
    the SDK Context already carries.
    """

    async def main():
        ctx = sdk_context.current()
        target_path = ctx.node.get("path")
        root = ctx.workspace
        cwd = ctx.cwd
        tokens = ctx.tokens
        req = sdk_context.request()

        # Host logic, expressed purely through the SDK context
        assert target_path == "/crm/contact/add"
        assert root == "/tmp/workspace"
        assert cwd == "/crm/contact"
        assert tokens == ["/crm/contact/add", "jane"]
        assert req.arg(0) == "jane"

        yield Pulse(effects=[EmitView(view={"kind": "text", "text": "host-ok"})])
        yield Pulse()

    _set_test_context()
    node = _make_node(main)

    from support.flow import make_flow

    flow = make_flow(node.run, session=harness.session)
    harness.scheduler.schedule_flow(flow, harness.session)

    projections = effect_executor._on_projection

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    views = [c.kwargs["document"] for c in projections.call_args_list]
    assert views == [{"kind": "text", "text": "host-ok"}]
