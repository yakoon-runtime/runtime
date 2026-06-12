from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from y5n.base.flow.channel import Scope
from y5n.base.flow.dsl import receive, start_cmd
from y5n.base.flow.primitives import AwaitEvent, Outcome, Stop
from y5n.base.nodes import Node
from y5n.base.runtime import Event


@pytest.mark.asyncio
async def test_command_resolves_and_dispatches_subflow(harness):
    """start_cmd resolviert den Command zu einem Node,
    dispatched einen Sub-Flow und leitet dessen Projektion
    auf den angegebenen Channel um."""

    received: list[object] = []
    created_flow = None

    async def sub_handler(ctx):
        from y5n.base.flow.dsl import out
        from y5n.base.projection import Projection

        yield out(Projection.create(blocks=[]))
        yield Outcome()

    sub_node = Node(key="test", run=sub_handler)

    # Echter Parser: Command-String in cmd + tokens zerlegen
    def parse_input(*, event):
        cmd, *rest = event.payload.strip().split()
        return cmd, rest, []

    # Echter Resolver: matcht "test" auf den sub_node
    def resolve_node(*, parent, key, tokens, session):
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

    harness.engine.on_start_command = on_start_command

    async def caller(ctx):
        ch = uuid4().hex
        yield start_cmd("test", channel=ch)
        yield Outcome()

        event = yield receive(ch, scope=Scope.SESSION)
        received.append(event.payload)
        yield Outcome()

    flow = await harness.start(caller)

    # Parent blockt auf receive
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)

    # Sub-Flow wurde erzeugt und eingeplant
    assert created_flow is not None
    assert created_flow.node is sub_node
    assert created_flow.out_channel is not None

    # Sub-Flow ausführen → Projektion wird auf den Channel umgeleitet
    outcome = await harness.run_until_blocked(created_flow)
    assert isinstance(outcome.control, Stop)

    # Parent hat jetzt die Projektion im Channel
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)
    assert len(received) == 1


@pytest.mark.asyncio
async def test_command_unresolvable_sends_none(harness):
    """Ein nicht auflösbarer Command sendet None auf den Channel."""

    received: list[object] = []

    def parse_input(*, event):
        cmd, *rest = event.payload.strip().split()
        return cmd, rest, []

    def resolve_node(*, parent, key, tokens, session):
        # Kein Node für "unknown" → Auflösung fehlschlagen
        return None, tokens or []

    harness.engine.on_parse_input = parse_input
    harness.engine.on_resolve_command = resolve_node

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

    harness.engine.on_start_command = on_start_command

    async def caller(ctx):
        ch = uuid4().hex
        yield start_cmd("unknown", channel=ch)
        yield Outcome()

        event = yield receive(ch, scope=Scope.SESSION)
        received.append(event.payload)
        yield Outcome()

    flow = await harness.start(caller)

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, AwaitEvent)

    # Event liegt bereits im Channel → on_enter hat Flow rescheduled
    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)
    assert received == [None]
