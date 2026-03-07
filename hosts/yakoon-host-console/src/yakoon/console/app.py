import asyncio

from yakoon.base import ports
from yakoon.base.capabilities.identity import PermissionService
from yakoon.base.runtime.sessions import SessionService
from yakoon.base.values import Key
from yakoon.compose.demo_data import seed_demo_system_data
from yakoon.compose.engine import compose_engine, initialize_storage
from yakoon.console.host.console import ConsoleHost
from yakoon.console.host.output import ConsoleOutput
from yakoon.platform.hosts.adapter import FormInput, InputEvent, TextInput
from yakoon.platform.hosts.runner import Runner


async def run_console() -> None:

    engine = compose_engine(
        plugins=[
            "yakoon.shell",
            "yakoon.auth",
            "yakoon.discovery",
            "yakoon.crm",
            "yakoon.office",
            "yakoon.workflow",
        ]
    )

    await initialize_storage(engine.services)
    await seed_demo_system_data(engine.services)

    sessions = engine.services.get(SessionService)
    session, _ = await sessions.get_or_create(
        Key.from_parts("system", "session", "develop", "1")
    )

    session.bind_io(ConsoleOutput())
    # session.set_output_stream_policy(OutputStreamPolicy(enabled=True))

    permissions = engine.services.get(PermissionService)
    permissions.set_bootstrap_permissions(session)

    runner: Runner | None = None

    async def submit(event: InputEvent) -> None:
        assert runner is not None
        if isinstance(event, FormInput):
            await runner.on_input_submit(event.data)
        elif isinstance(event, TextInput):
            await runner.on_user_input(event.value)

    try:
        host = ConsoleHost(submit=submit)
        runner = Runner(engine=engine, session=session, host=host)

        inits: list[str] = []
        # inits = ["use crm-customer", "customer-create"]
        await runner.start(inits)

    except KeyboardInterrupt:
        dialogs = engine.services.get(ports.DialogService)
        if dialogs.is_waiting(session):
            await runner.on_cancel()  # type: ignore[union-attr]
    finally:
        sessions.release(session.key)


if __name__ == "__main__":
    asyncio.run(run_console())
