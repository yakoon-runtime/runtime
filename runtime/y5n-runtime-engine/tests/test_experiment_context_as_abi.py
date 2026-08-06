"""Phase 3a experiment (ADR-12): the engine sets the invocation context.

The engine owns the invocation ABI. In ``CommandEngine._next_step`` it
builds the raw context dict from node + session + flow and sets it once —
no more hand-built translation in the host.

These tests verify that the *engine* sets a context a parameterless
``main()`` can read: a real node tree (``/crm/contact/add``), session data
(workspace, cwd, identity), and flow tokens — and ``main()`` sees exactly
those values via ``context.current()``.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.primitives import AwaitEvent, EmitView, Pulse, Stop
from y5n.runtime.api.naming import Key
from y5n.runtime.engine.nodes import Node
from y5n.runtime.api.runtime import Event
from y5n.runtime.engine.flow import Flow, FlowCursor
from y5n.runtime.engine.runtime.invocation import derive_invocation_context
from y5n.runtime.engine.runtime.sessions.session import Session
from y5n.sdk import context as sdk_context


def _build_add_node() -> Node:
    """Build /crm/contact/add as a real node tree."""
    add = Node(key="add", run=None)
    contact = Node(key="contact")
    contact.mount(add)
    crm = Node(key="crm")
    crm.mount(contact)
    return add


def _prepare_session(session: Session) -> None:
    """Fill the session with invocation-relevant data."""
    session.set_data("fs:root", "/tmp/workspace")
    session.set_cwd("/crm/contact")
    session.set_identity(Key.from_parts("users", "user", "global", "u-1"), "alice")


def _make_node(main) -> Node:
    node = _build_add_node()
    node.run = main
    return node


def _make_flow(node: Node, session: Session, tokens=None, payload="test"):
    flow_id = session.next_flow_id()
    flow = Flow(
        id=flow_id,
        node=node,
        event=Event(payload=payload),
        cursor=FlowCursor("run"),
        tokens=tokens or ["jane"],
        invocation=derive_invocation_context(
            node=node, session=session, flow_id=flow_id, tokens=tokens or ["jane"]
        ),
    )
    session.add_flow(flow)
    return flow


@pytest.mark.asyncio
async def test_engine_sets_invocation_context(harness, effect_executor):
    """The engine builds the context; a parameterless main() reads it."""

    async def main():
        ctx = sdk_context.current()
        assert ctx.node.get("path") == "/crm/contact/add"
        assert ctx.node.get("name") == "add"
        assert ctx.workspace == "/tmp/workspace"
        assert ctx.cwd == "/crm/contact"
        assert ctx.args == ["jane"]

        req = sdk_context.request()
        assert req.arg(0) == "jane"

        session = sdk_context.session()
        assert session.key == "test/session/runtime#test-1"
        assert session.user == "alice"
        assert session.user_id == "users/user/global#u-1"

        flow = sdk_context.flow()
        assert flow.key == "add"

        yield Pulse(effects=[EmitView(view={"kind": "text", "text": "ok"})])
        yield Pulse()

    _prepare_session(harness.session)
    node = _make_node(main)
    flow = _make_flow(node, harness.session)
    harness.scheduler.schedule_flow(flow, harness.session)

    projections = effect_executor._on_projection

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    views = [c.kwargs["document"] for c in projections.call_args_list]
    assert views == [{"kind": "text", "text": "ok"}]


@pytest.mark.asyncio
async def test_engine_context_prompt_round_trip(harness, effect_executor):
    """Engine-set context: write → AwaitEvent → reply → stop."""

    async def main():
        yield Pulse(effects=[EmitView(view={"kind": "text", "text": "write-view"})])
        event = yield Pulse(control=AwaitEvent("__user__", scope=Scope.USER_INPUT))
        assert event is not None
        yield Pulse(
            effects=[EmitView(view={"kind": "text", "text": f"got:{event.payload}"})]
        )
        yield Pulse()

    node = _make_node(main)
    flow = _make_flow(node, harness.session)
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
async def test_engine_context_empty_session_defaults(harness, effect_executor):
    """A bare session still yields a usable (defaulted) context."""

    async def main():
        ctx = sdk_context.current()
        assert ctx.node.get("path") == "/crm/contact/add"
        assert ctx.workspace == ""
        assert ctx.cwd == ""

        yield Pulse(effects=[EmitView(view={"kind": "text", "text": "bare"})])
        yield Pulse()

    node = _make_node(main)
    flow = _make_flow(node, harness.session)
    harness.scheduler.schedule_flow(flow, harness.session)

    projections = effect_executor._on_projection

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    views = [c.kwargs["document"] for c in projections.call_args_list]
    assert views == [{"kind": "text", "text": "bare"}]
