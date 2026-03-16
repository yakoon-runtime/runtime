import asyncio

from yakoon.base.capabilities.identity import PermissionService
from yakoon.base.runtime import SessionService
from yakoon.base.values import Key
from yakoon.compose.demo_data import seed_demo_system_data
from yakoon.compose.engine import compose_engine, initialize_storage
from yakoon.console.client import ConsoleClient
from yakoon.platform.host import RuntimeHost
from yakoon.platform.runtime.bus import BusOutput, SessionBus
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

    sessions = engine.services.get(SessionService)

    session, _ = await sessions.get_or_create(
        Key.from_parts("system", "session", "develop", "1")
    )

    permissions = engine.services.get(PermissionService)
    permissions.set_bootstrap_permissions(session)

    # -------------------------------------------------
    # Host runtime
    # -------------------------------------------------

    bus = SessionBus()

    session.bind_io(BusOutput(bus))

    host = RuntimeHost(
        engine=engine,
        session=session,
        bus=bus,
    )

    transport = LocalTransport(host)

    # -------------------------------------------------
    # Client
    # -------------------------------------------------

    client = ConsoleClient(transport)

    try:
        await client.run()

    finally:
        sessions.release(session.key)


if __name__ == "__main__":

    try:
        asyncio.run(run_console())
    except KeyboardInterrupt:
        pass
