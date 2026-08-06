from __future__ import annotations

from uuid import uuid4

import pytest
from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.dsl import out, receive, start_cmd
from y5n.runtime.api.flow.primitives import AwaitEvent, Pulse, StartCommand, Stop
from y5n.runtime.engine.nodes import Node
from y5n.runtime.api.runtime import Event
from y5n.runtime.engine.machine.effects import StartCommandHandler


@pytest.mark.asyncio
async def test_command_channel_contract(harness):
    """start_cmd dispatches a sub-flow; the caller receives
    the result on the configured SESSION channel."""

    received: list[object] = []

    async def sub_flow():
        yield out({"kind": "document", "header": {"role": "info"}, "blocks": []})
        yield Pulse()

    async def caller():
        ch = uuid4().hex
        yield start_cmd("test", channel=ch)
        yield Pulse()

        event = yield receive(ch, scope=Scope.SESSION)
        received.append(event.payload)
        yield Pulse()

    sub_node = Node(key="test", run=sub_flow)

    async def resolve(parent, key, tokens, session, strict=True):
        return sub_node, tokens or []

    harness.engine.on_resolve_node = resolve

    flow = await harness.start(caller)

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, AwaitEvent)

    # Simulate sub-flow result on the channel
    harness.send_session(pulse.control.channel, {"done": True})

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)

    assert received == [{"done": True}]


@pytest.mark.asyncio
async def test_start_cmd_parses_tokens(harness, effect_executor):
    """start_cmd("test --flag value") zerlegt den Command-String
    in cmd + args und übergibt die Tokens an den Sub-Flow."""

    received_tokens: list[list[str]] = []
    created_flow = None

    async def sub_handler():
        from y5n.sdk import context

        received_tokens.append(context.request().args())
        yield out({"kind": "document", "header": {"role": "info"}, "blocks": []})
        yield Pulse()

    sub_node = Node(key="test", run=sub_handler)

    def parse_input(*, event):
        cmd, *rest = event.payload.strip().split()
        return cmd, rest, []

    def resolve_node(*, key, tokens, session, strict=True):
        if key == "test":
            return sub_node, tokens or []
        return None, tokens or []

    harness.engine.on_parse_input = parse_input
    harness.engine.on_resolve_command = resolve_node

    async def on_start_command(*, command, channel, flow, session, remote=None):
        nonlocal created_flow
        event = Event(payload=command)
        new_flow = await harness.engine.dispatch(session=session, event=event)
        if new_flow is not None:
            new_flow.out_channel = channel
            created_flow = new_flow
            harness.scheduler.schedule_flow(new_flow, harness.session)
        else:
            harness.send_session(channel, None)

    effect_executor.register(
        StartCommand,
        StartCommandHandler(on_start_command),
    )

    async def caller():
        ch = uuid4().hex
        yield start_cmd("test --flag value", channel=ch)
        yield Pulse()
        yield receive(ch, scope=Scope.SESSION)
        yield Pulse()

    flow = await harness.start(caller)

    # Parent: yield start_cmd + yield Pulse → blocked on receive
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, AwaitEvent)

    # Sub-flow was created with correct tokens
    assert created_flow is not None
    assert created_flow.tokens == ["--flag", "value"]

    # Run the sub-flow
    pulse = await harness.run_until_blocked(created_flow)
    assert isinstance(pulse.control, Stop)

    # Sub-Flow hat Tokens via ctx.request.args() erhalten
    assert received_tokens == [["--flag", "value"]]

    # The parent was woken by _schedule_waiting
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
