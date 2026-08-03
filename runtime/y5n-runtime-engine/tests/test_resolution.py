from __future__ import annotations

from uuid import uuid4

import pytest
from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.dsl import receive, start_cmd
from y5n.runtime.api.flow.primitives import AwaitEvent, Pulse, StartCommand, Stop
from y5n.runtime.api.nodes import Node
from y5n.runtime.api.runtime import Event
from y5n.runtime.engine.machine.effects import StartCommandHandler


@pytest.mark.asyncio
async def test_command_resolves_and_dispatches_subflow(harness, effect_executor):
    """start_cmd resolviert den Command zu einem Node,
    dispatched einen Sub-Flow und leitet dessen Projektion
    auf den angegebenen Channel um."""

    received: list[object] = []
    created_flow = None

    async def sub_handler(ctx):
        from y5n.runtime.api.flow.dsl import out

        yield out({"kind": "document", "header": {"role": "info"}, "blocks": []})
        yield Pulse()

    sub_node = Node(key="test", run=sub_handler)

    # Echter Parser: Command-String in cmd + tokens zerlegen
    def parse_input(*, event):
        cmd, *rest = event.payload.strip().split()
        return cmd, rest, []

    # Echter Resolver: matcht "test" auf den sub_node
    def resolve_node(*, key, tokens, session, strict=True):
        if key == "test":
            return sub_node, tokens or []
        return None, tokens or []

    harness.engine.on_parse_input = parse_input
    harness.engine.on_resolve_command = resolve_node

    # Echter on_start_command: dispatch + schedule
    async def on_start_command(*, command, channel, flow, session, remote=None):
        nonlocal created_flow
        event = Event(payload=command)
        new_flow = await harness.engine.dispatch(session=session, event=event)
        if new_flow is not None:
            new_flow.out_channel = channel
            created_flow = new_flow
            harness.scheduler.schedule_flow(new_flow, harness.session)

    effect_executor.register(
        StartCommand,
        StartCommandHandler(on_start_command),
    )

    async def caller(ctx):
        ch = uuid4().hex
        yield start_cmd("test", channel=ch)
        yield Pulse()

        event = yield receive(ch, scope=Scope.SESSION)
        received.append(event.payload)
        yield Pulse()

    flow = await harness.start(caller)

    # Parent blockt auf receive
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, AwaitEvent)

    # Sub-flow was created and scheduled
    assert created_flow is not None
    assert created_flow.node is sub_node
    assert created_flow.out_channel is not None

    # Run the sub-flow: the projection is redirected to the channel
    pulse = await harness.run_until_blocked(created_flow)
    assert isinstance(pulse.control, Stop)

    # The parent now has the projection in the channel
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    assert len(received) == 1


@pytest.mark.asyncio
async def test_command_unresolvable_sends_none(harness, effect_executor):
    """An unresolvable command sends None to the channel."""

    received: list[object] = []

    def parse_input(*, event):
        cmd, *rest = event.payload.strip().split()
        return cmd, rest, []

    def resolve_node2(*, key, tokens, session, strict=True):
        # No node for "unknown" → resolution fails
        return None, tokens or []

    harness.engine.on_parse_input = parse_input
    harness.engine.on_resolve_command = resolve_node2

    async def on_start_command(*, command, channel, flow, session, remote=None):
        event = Event(payload=command)
        try:
            new_flow = await harness.engine.dispatch(session=session, event=event)
            if new_flow is not None:
                new_flow.out_channel = channel
                harness.scheduler.schedule_flow(new_flow, harness.session)
            else:
                harness.send_session(channel, None)
        except Exception:
            harness.send_session(channel, None)

    effect_executor.register(
        StartCommand,
        StartCommandHandler(on_start_command),
    )

    async def caller(ctx):
        ch = uuid4().hex
        yield start_cmd("unknown", channel=ch)
        yield Pulse()

        event = yield receive(ch, scope=Scope.SESSION)
        received.append(event.payload)
        yield Pulse()

    flow = await harness.start(caller)

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, AwaitEvent)

    # Event liegt bereits im Channel → on_enter hat Flow rescheduled
    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    assert received == [None]
