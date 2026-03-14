import asyncio

from yakoon.base.capabilities.identity import PermissionService
from yakoon.base.capabilities.interaction import DialogService
from yakoon.base.runtime import SessionService
from yakoon.base.ui import OutputStreamPolicy
from yakoon.base.values import Key
from yakoon.compose.demo_data import seed_demo_system_data
from yakoon.compose.engine import compose_engine, initialize_storage
from yakoon.console.host import ConsoleHost
from yakoon.console.output import ConsoleOutput
from yakoon.console.ui import TerminalSurface, TerminalUI
from yakoon.platform.hosts import FormInput, InputEvent, Runner, TextInput


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

    surface = TerminalSurface()

    output = ConsoleOutput(surface)
    session.bind_io(output)
    session.set_output_stream_policy(OutputStreamPolicy(enabled=True))

    permissions = engine.services.get(PermissionService)
    permissions.set_bootstrap_permissions(session)

    runner: Runner | None = None

    async def submit(event: InputEvent) -> None:
        assert runner is not None
        if isinstance(event, FormInput):
            await runner.on_input_submit(event.data)
        elif isinstance(event, TextInput):
            await runner.on_user_input(event.value)

    async def cancel():
        await output.cancel()
        dialogs = engine.services.get(DialogService)
        if dialogs.is_waiting(session):
            if runner is not None:
                await runner.on_cancel()

        session.mark("exit_app")

    try:
        ui = TerminalUI(surface, on_cancel=cancel)
        host = ConsoleHost(ui=ui, submit=submit)
        runner = Runner(engine=engine, session=session, host=host, interact=ui)

        inits: list[str] = []
        # inits = ["use crm-customer", "customer-create"]

        runner_task = asyncio.create_task(runner.start(inits))
        ui_task = asyncio.create_task(ui.run())

        _, pending = await asyncio.wait(
            [runner_task, ui_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        await asyncio.gather(*pending, return_exceptions=True)
        await host.on_exit()

    except KeyboardInterrupt:
        await cancel()

    finally:
        sessions.release(session.key)


if __name__ == "__main__":
    try:
        asyncio.run(run_console())
    except KeyboardInterrupt:
        pass
