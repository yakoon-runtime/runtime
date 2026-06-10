from __future__ import annotations

import time
from uuid import uuid4

import pytest
from y5n.base.flow.channel import Scope
from y5n.base.flow.dsl import out, receive, send, start_cmd
from y5n.base.flow.primitives import Outcome, Stop
from y5n.base.nodes import Node
from y5n.base.projection import Projection
from y5n.base.runtime import Event

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
        outcome = await engine.step_flow(flow, session)
        steps += 1
        if outcome is not None:
            if isinstance(outcome.control, Stop):
                break
            await scheduler._handle_outcome(session, flow, outcome)
    return steps


# ----------------------------------------------------------------
# B1 — Flow-Switches
# ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_flow_switches(harness):
    """Benchmark: reine Outcome-Iterationen (Engine + Scheduler, kein IO)."""

    N = 10_000

    async def handler(ctx):
        for _ in range(N):
            yield Outcome()

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
    """Benchmark: send/receive über SESSION-Channel."""

    N = 5_000
    ch = uuid4().hex
    received = 0

    async def receiver(ctx):
        nonlocal received
        for _ in range(N):
            event = yield receive(ch, scope=Scope.SESSION)
            received += 1

    async def sender(ctx):
        for _ in range(N):
            yield send(ch, Event(payload="p"), scope=Scope.SESSION)
        yield Outcome()

    rx = await harness.start(receiver)
    tx = await harness.start(sender)

    start = time.monotonic()

    outcome = await harness.run_until_stop(tx)
    assert isinstance(outcome.control, Stop)

    outcome = await harness.run_until_stop(rx)
    assert isinstance(outcome.control, Stop)

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
    """Benchmark: wartende Flows, dann ein Wake."""

    N = 10_000
    ch = uuid4().hex
    woke = 0

    async def waiter(ctx):
        nonlocal woke
        event = yield receive(ch, scope=Scope.SESSION)
        woke += 1
        yield Outcome()

    flows = []

    t0 = time.monotonic()
    for i in range(N):
        if i % 1000 == 0:
            print(f"  creating flow {i}/{N} ...")
        flow = await harness.start(waiter)
        outcome = await harness.run_until_blocked(flow)
        flows.append(flow)

    t1 = time.monotonic()
    print(f"  created {N} flows in {t1 - t0:.3f}s")

    start = time.monotonic()

    harness.send_session(ch, "wake")
    scheduler._schedule_waiting(harness.session, ch)

    for flow in flows:
        if flow.scheduled:
            await harness.run_until_blocked(flow)
            break

    elapsed = time.monotonic() - start

    print()
    print(_label("Massive-Parallel (1 wake von 10k)", N, elapsed))
    print(f"  woke={woke}")


# ----------------------------------------------------------------
# B4 — Runtime-Mix
# ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_runtime_mix(harness):
    """Benchmark: gemischte Last aus receive, send, start_cmd, Outcome."""

    N = 1_000
    sub_ch = uuid4().hex

    async def sub_handler(ctx):
        yield out(Projection.create(blocks=[]))
        yield Outcome()

    sub_node = Node(key="sub", run=sub_handler)

    def parse_input(*, event):
        cmd, *rest = event.payload.strip().split()
        return cmd, rest, []

    def resolve_node(*, parent, key, tokens, session):
        if key == "sub":
            return sub_node, tokens or []
        return None, tokens or []

    harness.engine.on_parse_input = parse_input
    harness.engine.on_resolve_command = resolve_node

    async def on_start_command(*, command, channel, flow, session):
        new_flow = await harness.engine.dispatch(session=session, event=Event(payload=command))
        if new_flow is not None:
            new_flow.out_channel = channel
            harness.scheduler.schedule_flow(new_flow, harness.session)
        else:
            harness.send_session(channel, None)

    harness.engine.on_start_command = on_start_command

    async def main_handler(ctx):
        for _ in range(N):
            yield send("mix", Event(payload="data"), scope=Scope.SESSION)
            if _ % 2 == 0:
                yield start_cmd("sub", channel=sub_ch)
                yield receive(sub_ch, scope=Scope.SESSION)
            yield Outcome()

    flow = await harness.start(main_handler)

    start = time.monotonic()
    outcome = await harness.run_until_stop(flow)
    assert isinstance(outcome.control, Stop)
    elapsed = time.monotonic() - start

    print()
    print(_label("Runtime-Mix (send+start_cmd+receive+outcome)", N, elapsed))
