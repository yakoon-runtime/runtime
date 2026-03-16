import asyncio

from yakoon.base.capabilities.interaction import DialogService
from yakoon.base.interaction import ClientConnection
from yakoon.base.ui.stream import OutputStreamPolicy
from yakoon.console.host import ConsoleHost
from yakoon.console.output import ConsoleOutput
from yakoon.console.ui import TerminalSurface, TerminalUI
from yakoon.platform.hosts import FormInput, InputEvent, Runner, TextInput


class ConsoleClient:

    def __init__(self, engine, session, bus):
        self.engine = engine
        self.session = session
        self.bus = bus

    async def run(self):

        surface = TerminalSurface()
        renderer = ConsoleOutput(surface)

        # ---------------------------------------------
        # receive events from SessionBus
        # ---------------------------------------------

        async def on_event(event):
            await renderer.view(event)

        connection = ClientConnection(
            on_event,
            renderer.set_flow_control,
        )

        self.bus.join(connection)

        # ---------------------------------------------
        # session config
        # ---------------------------------------------

        self.session.set_output_stream_policy(OutputStreamPolicy(enabled=True))

        runner: Runner | None = None

        async def submit(event: InputEvent):
            assert runner is not None
            if isinstance(event, FormInput):
                await runner.on_input_submit(event.data)
            elif isinstance(event, TextInput):
                await runner.on_user_input(event.value)

        async def cancel():

            dialogs = self.engine.services.get(DialogService)

            if dialogs.is_waiting(self.session):
                if not runner:
                    raise RuntimeError("Runner must not be None")
                await runner.on_cancel()
                return

            self.session.mark("exit_app")
            ui.app.exit()

        # ---------------------------------------------
        # UI
        # ---------------------------------------------

        ui = TerminalUI(surface, on_cancel=cancel)

        host = ConsoleHost(ui=ui, submit=submit)

        runner = Runner(
            engine=self.engine,
            session=self.session,
            host=host,
            interact=ui,
        )

        # ---------------------------------------------
        # runtime tasks
        # ---------------------------------------------

        async with asyncio.TaskGroup() as tg:
            tg.create_task(runner.start([]))
            tg.create_task(renderer.run())
            tg.create_task(ui.run())

        await host.on_exit()

        self.bus.leave(connection)
