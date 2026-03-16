import asyncio

from yakoon.compose.demo_data import seed_demo_system_data
from yakoon.compose.engine import compose_engine, initialize_storage
from yakoon.console.client import ConsoleClient
from yakoon.platform.host import RuntimeHost
from yakoon.platform.runtime.bus import SessionBus
from yakoon.platform.transport import LocalTransport


async def run_console() -> None:

    engine = compose_engine(
        plugins=[
            "yakoon.shell",
            "yakoon.crm",
            "yakoon.office",
        ],
        capabilities={
            "audit": "default",
            "discovery": "default",
            "identity": "default",
            "interaction": "default",
            "presenters": "default",
            "workflow": "default",
        },
    )

    await initialize_storage(engine.services)
    await seed_demo_system_data(engine.services)

    # -------------------------------------------------
    # Host runtime
    # -------------------------------------------------

    bus = SessionBus()

    host = RuntimeHost(
        engine=engine,
        bus=bus,
    )

    transport = LocalTransport(host)

    # -------------------------------------------------
    # Client
    # -------------------------------------------------

    client = ConsoleClient(transport)
    await client.run()


if __name__ == "__main__":

    try:
        asyncio.run(run_console())
    except KeyboardInterrupt:
        pass
