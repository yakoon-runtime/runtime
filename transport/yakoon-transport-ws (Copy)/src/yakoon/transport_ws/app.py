import asyncio

import websockets
from host.connection import WebSocketConnection
from host.runner import handle

from yakoon.compose.demo_data import seed_demo_system_data
from yakoon.compose.engine import compose_engine, initialize_storage
from yakoon.platform.machine import RuntimeHost
from yakoon.platform.runtime.bus import SessionBus


async def run_console() -> None:

    engine = compose_engine(
        plugins=[
            "yakoon.shell",
            "yakoon.crm",
            "yakoon.office",
            "yakoon.playground",
        ],
        capabilities={
            "audit": "default",
            "discovery": "default",
            "identity": "default",
            "interaction": "default",
            "jobs": "default",
            "workflow": "default",
        },
    )

    await initialize_storage(engine.container)
    await seed_demo_system_data(engine.container)

    # -------------------------------------------------
    # Host runtime
    # -------------------------------------------------

    bus = SessionBus()

    host = RuntimeHost(
        engine=engine,
        bus=bus,
    )

    async def _handler(ws):
        connection = WebSocketConnection(ws)
        await handle(host, connection, ws)

    async with websockets.serve(_handler, "localhost", 8765):
        await asyncio.Future()  # läuft für immer

    # transport = LocalTransport(host)

    # -------------------------------------------------
    # Client
    # -------------------------------------------------

    # client = ConsoleClient(transport)
    # await client.run()


if __name__ == "__main__":

    try:
        asyncio.run(run_console())
    except KeyboardInterrupt:
        pass
