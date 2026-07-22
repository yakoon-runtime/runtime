#!/usr/bin/env python3
"""Test: Runtime-to-Runtime command execution + Projection Streaming.

Starts two runtimes (B on 9101, A on 9100).
On A, typing "call" runs "hello" on B (simple remote cmd).
On A, typing "stream" runs a streaming flow on B that yields
projections with delays — proves real-time projection forwarding.

Usage:
  python scripts/test-remote.py
  # Connect Texture to ws://localhost:9100
  # Type "call"   → remote hello on B
  # Type "stream" → remote stream (1..2..3 with 1s delays)
"""

import asyncio
import uuid

from websockets.asyncio.server import serve
from y5n.runtime.api.flow.dsl import delay, out_text, start_cmd
from y5n.runtime.api.flow.primitives import Outcome
from y5n.runtime.api.nodes import Node
from y5n.runtime.engine.settings import RuntimeSettings, Settings
from y5n.runtime.engine.wire.runtime import build_runtime
from y5ntrans.websocket.server import WebSocketServerTransport


async def main():
    # ────────── Runtime B (remote, port 9101) ──────────
    async def hello_flow(ctx):
        yield out_text("Hello from Runtime B!")
        yield Outcome()

    async def stream_flow(ctx):
        yield out_text("1")
        yield delay(1)
        yield out_text("2")
        yield delay(1)
        yield out_text("3")
        yield Outcome()

    runtime_b = build_runtime(
        settings=Settings(),
        nodes=[
            Node(
                key="hello",
                run=hello_flow,
                anonymous=True,  # GLOBAL
                resolvable=True,
            ),
            Node(
                key="stream",
                run=stream_flow,
                anonymous=True,  # GLOBAL
                resolvable=True,
            ),
        ],
    )
    await runtime_b.setup()

    async def handler_b(ws):
        transport = WebSocketServerTransport(runtime_b)
        _, recv = await transport.connect(ws)
        await recv()

    # ────────── Runtime A (local, port 9100) ──────────
    async def call_flow(ctx):
        ch = uuid.uuid4().hex
        yield out_text("── Calling Runtime B (hello) ──")
        yield start_cmd("hello", channel=ch, remote="office")
        yield out_text("── Done ──")
        yield Outcome()

    async def stream_remote_flow(ctx):
        ch = uuid.uuid4().hex
        yield out_text("── Calling Runtime B (stream) ──", mode="append")
        yield start_cmd("stream", channel=ch, remote="office")
        yield out_text("── Stream done ──", mode="append")
        yield Outcome()

    runtime_a = build_runtime(
        spaces=["y5nspace.shell"],
        settings=Settings(
            runtime=RuntimeSettings(known={"office": "ws://localhost:9101"})
        ),
        nodes=[
            Node(
                key="call",
                run=call_flow,
                anonymous=True,  # GLOBAL
                resolvable=True,
            ),
            Node(
                key="stream",
                run=stream_remote_flow,
                anonymous=True,  # GLOBAL
                resolvable=True,
            ),
        ],
    )
    await runtime_a.setup()

    async def handler_a(ws):
        transport = WebSocketServerTransport(runtime_a)
        _, recv = await transport.connect(ws)
        await recv()

    # ────────── Serve ──────────
    async with serve(handler_b, "0.0.0.0", 9101), serve(handler_a, "0.0.0.0", 9100):
        print("=" * 55)
        print("Runtimes ready:")
        print("  A: ws://localhost:9100")
        print("  B: ws://localhost:9101")
        print()
        print("Type on A:")
        print("  'call'   → runs 'hello' on B (simple)")
        print("  'stream' → runs 'stream' on B (1..2..3)")
        print()
        print("Stream should appear with 1s delays,")
        print("projected in real-time from B to A.")
        print("=" * 55)
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
