from __future__ import annotations

from uuid import uuid4

import pytest
from y5n.base.flow.channel import Scope
from y5n.base.flow.dsl import out, receive, start_cmd
from y5n.base.flow.primitives import AwaitEvent, Outcome, StartCommand, Stop
from y5n.base.nodes import Node
from y5n.base.projection import Projection
from y5n.base.runtime import Event
from y5n.runtime.machine.effects import StartCommandHandler


@pytest.mark.asyncio
async def test_command_channel_contract(harness):
    """start_cmd dispatches a sub-flow; the caller receives
    the result on the configured SESSION channel."""

    received: list[object] = []

    async def sub_flow(ctx):
        yield out(Projection.create(blocks=[]))
        yield Outcome()

    async def caller(ctx):
        ch = uuid4().hex
        yield start_cmd("test", channel=ch)
        yield Outcome()

        event = yield receive(ch, scope=Scope.SESSION)
        received.append(event.payload)
        yield Outcome()

    sub_node = Node(key="test", run=sub_flow)

    async def resolve(parent, key, tokens, session, strict=True):
        return sub_node, tokens or []

    harness.engine.on_resolve_node = resolve

    flow = await harness.start(caller)

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)

    # Simulate sub-flow result on the channel
    harness.send_session(outcome.control.channel, {"done": True})

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)

    assert received == [{"done": True}]


@pytest.mark.asyncio
async def test_start_cmd_parses_tokens(harness, effect_executor):
    """start_cmd("test --flag value") zerlegt den Command-String
    in cmd + args und übergibt die Tokens an den Sub-Flow."""

    received_tokens: list[list[str]] = []
    created_flow = None

    async def sub_handler(ctx):
        received_tokens.append(ctx.request.args())
        yield out(Projection.create(blocks=[]))
        yield Outcome()

    sub_node = Node(key="test", run=sub_handler)

    def parse_input(*, event):
        cmd, *rest = event.payload.strip().split()
        return cmd, rest, []

    def resolve_node(*, parent, key, tokens, session, strict=True):
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

    async def caller(ctx):
        ch = uuid4().hex
        yield start_cmd("test --flag value", channel=ch)
        yield Outcome()
        yield receive(ch, scope=Scope.SESSION)
        yield Outcome()

    flow = await harness.start(caller)

    # Parent: yield start_cmd + yield Outcome → blocked on receive
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)

    # Sub-Flow wurde erzeugt mit korrekten Tokens
    assert created_flow is not None
    assert created_flow.tokens == ["--flag", "value"]

    # Sub-Flow ausführen
    outcome = await harness.run_until_blocked(created_flow)
    assert isinstance(outcome.control, Stop)

    # Sub-Flow hat Tokens via ctx.request.args() erhalten
    assert received_tokens == [["--flag", "value"]]

    # Parent wurde durch _schedule_waiting aufgeweckt
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)
