from __future__ import annotations

import time
from uuid import uuid4

import pytest
from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.dsl import out, receive, send, start_cmd
from y5n.runtime.api.flow.primitives import Pulse, StartCommand, Stop
from y5n.runtime.engine.nodes import Node
from y5n.runtime.api.runtime import Event
from y5n.runtime.engine.flow import Flow
from y5n.runtime.engine.machine.effects import StartCommandHandler

pytestmark = pytest.mark.benchmark


# ----------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------


def _label(label: str, n: int, elapsed: float) -> str:
    ops = n / elapsed if elapsed > 0 else 0
    return f"{label}: {n} ops in {elapsed:.4f}s \u2192 {ops:,.0f} ops/s"


async def _drive_to_stop(engine, scheduler, session, flow):
    """Drive a single flow to Stop, counting engine steps."""
    steps = 0
    while True:
        pulse = await engine.step_flow(flow, session)
        steps += 1
        if pulse is not None:
            if isinstance(pulse.control, Stop):
                break
            await scheduler._handle_pulse(session, flow, pulse)
    return steps


# ----------------------------------------------------------------
# B1 — Flow-Switches
# ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_flow_switches(harness):
    """Benchmark: reine Pulse-Iterationen (Engine + Scheduler, kein IO)."""

    N = 10_000

    async def handler():
        for _ in range(N):
            yield Pulse()

    flow = await harness.start(handler)

    start = time.monotonic()
    steps = await _drive_to_stop(
        harness.engine, harness.scheduler, harness.session, flow
    )
    elapsed = time.monotonic() - start

    print()
    print(_label("Flow-Switches", N, elapsed))
    print(f"  Engine steps: {steps}")

    assert steps == N + 1


# ----------------------------------------------------------------
# B2 — Channel Throughput
# ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_session_channel_throughput(harness):
    """Benchmark: send/receive over the SESSION channel."""

    N = 5_000
    ch = uuid4().hex
    received = 0

    async def receiver():
        nonlocal received
        for _ in range(N):
            yield receive(ch, scope=Scope.SESSION)
            received += 1

    async def sender():
        for _ in range(N):
            yield send(ch, Event(payload="p"), scope=Scope.SESSION)
        yield Pulse()

    rx = await harness.start(receiver)
    tx = await harness.start(sender)

    start = time.monotonic()

    pulse = await harness.run_until_stop(tx)
    assert isinstance(pulse.control, Stop)

    pulse = await harness.run_until_stop(rx)
    assert isinstance(pulse.control, Stop)

    elapsed = time.monotonic() - start
    msgs = N

    print()
    print(_label("Session-Channel (send+receive)", msgs, elapsed))
    print(f"  received={received}")


# ----------------------------------------------------------------
# B3 — Massive Parallelität
# ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_massive_waiting_flows(harness, scheduler):
    """Benchmark: 10k / 50k / 100k wartende Flows, dann ein Wake."""

    for label, N in [("10k", 10_000), ("50k", 50_000), ("100k", 100_000)]:
        ch = uuid4().hex
        woke = 0

        async def waiter(_ch=ch):
            nonlocal woke
            yield receive(_ch, scope=Scope.SESSION)
            woke += 1
            yield Pulse()

        flows: list[Flow] = []
        t0 = time.monotonic()
        for _ in range(N):
            flow = await harness.start(waiter)
            await harness.run_until_blocked(flow)
            flows.append(flow)
        t1 = time.monotonic()

        harness.send_session(ch, "wake")
        t_wake_start = time.monotonic()
        scheduler._schedule_waiting(harness.session, ch)
        for flow in flows:
            if flow.scheduled:
                await harness.run_until_blocked(flow)
                break
        t_wake = time.monotonic() - t_wake_start

        create_rate = N / (t1 - t0) if (t1 - t0) > 0 else 0
        print(
            f"  {label}: create={t1-t0:.3f}s ({create_rate:,.0f} flows/s), wake={t_wake:.4f}s, woke={woke}"
        )


# ----------------------------------------------------------------
# B4 — Runtime-Mix
# ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_runtime_mix(harness, effect_executor):
    """Benchmark: gemischte Last aus receive, send, start_cmd, Pulse."""

    N = 1_000
    sub_ch = uuid4().hex

    async def sub_handler():
        yield out({"kind": "document", "header": {"role": "info"}, "blocks": []})
        yield Pulse()

    sub_node = Node(key="sub", run=sub_handler)

    def parse_input(*, event):
        cmd, *rest = event.payload.strip().split()
        return cmd, rest, []

    def resolve_node(*, key, tokens, session, strict=True):
        if key == "sub":
            return sub_node, tokens or []
        return None, tokens or []

    harness.engine.on_parse_input = parse_input
    harness.engine.on_resolve_command = resolve_node

    created_sub_flows: list[Flow] = []

    async def on_start_command(*, command, channel, flow, session, remote=None):
        new_flow = await harness.engine.dispatch(
            session=session, event=Event(payload=command)
        )
        if new_flow is not None:
            new_flow.out_channel = channel
            created_sub_flows.append(new_flow)
            harness.scheduler.schedule_flow(new_flow, harness.session)
        else:
            harness.send_session(channel, None)

    effect_executor.register(
        StartCommand,
        StartCommandHandler(on_start_command),
    )

    async def main_handler():
        for _ in range(N):
            yield send("mix", Event(payload="data"), scope=Scope.SESSION)
            if _ % 2 == 0:
                yield start_cmd("sub", channel=sub_ch)
                yield receive(sub_ch, scope=Scope.SESSION)
            yield Pulse()

    flow = await harness.start(main_handler)

    start = time.monotonic()

    while True:
        pulse = await harness.run_until_blocked(flow)
        if isinstance(pulse.control, Stop):
            break

        # Main flow awaits sub-flow results — drain created sub-flows
        while created_sub_flows:
            sub = created_sub_flows.pop(0)
            await harness.run_until_stop(sub)

    elapsed = time.monotonic() - start

    print()
    print(_label("Runtime-Mix (send+start_cmd+receive+pulse)", N, elapsed))
