#!/usr/bin/env python3
"""Start a headless runtime with WebSocket on a given port.

Usage:
    python scripts/serve-runtime.py 9100 "y5nspace.shell,y5nspace.os"
    python scripts/serve-runtime.py 9101 "y5nspace.shell,y5nspace.ident"
"""

import asyncio
import sys

from websockets.asyncio.server import serve
from y5n.runtime.settings import Settings
from y5n.runtime.wire.runtime import build_runtime
from y5ntrans.websocket.server import WebSocketServerTransport

HOST = "0.0.0.0"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9100
PLUGINS = (
    sys.argv[2].split(",")
    if len(sys.argv) > 2
    else [
        "y5nspace.shell",
        "y5nspace.os",
    ]
)


async def handler(websocket):
    transport = WebSocketServerTransport(host)
    _, recv = await transport.connect(websocket)
    await recv()


async def main():
    global host
    runtime = build_runtime(
        plugins=PLUGINS,
        capabilities={},
        settings=Settings(),
    )
    host = runtime
    await host.setup()

    print(f"Runtime ready on ws://{HOST}:{PORT}")
    print(f"  plugins: {PLUGINS}")

    async with serve(handler, HOST, PORT):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
